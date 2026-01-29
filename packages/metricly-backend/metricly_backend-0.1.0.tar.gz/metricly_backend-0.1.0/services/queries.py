"""Query services for metric execution and visualization suggestions.

Provides functions for querying metrics via MetricFlow, listing available
metrics and dimensions, and suggesting appropriate visualizations.
"""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Literal

from pydantic import BaseModel, Field


# Thread pool for running sync queries
_query_executor = ThreadPoolExecutor(max_workers=4)


# ============================================================================
# Pydantic Models
# ============================================================================


class QueryParams(BaseModel):
    """Input parameters for metric queries."""

    metrics: list[str] = Field(
        description="List of metric names to query (e.g., ['total_revenue', 'order_count'])"
    )
    dimensions: list[str] | None = Field(
        default=None,
        description="Dimensions to group by (e.g., ['customer_segment', 'region'])",
    )
    grain: Literal["day", "week", "month", "quarter", "year"] | None = Field(
        default=None,
        description="Time granularity for the query",
    )
    start_date: date | None = Field(
        default=None,
        description="Start date for the query",
    )
    end_date: date | None = Field(
        default=None,
        description="End date for the query",
    )
    limit: int | None = Field(
        default=None,
        description="Maximum number of rows to return",
    )
    order_by: str | None = Field(
        default=None,
        description="Column to sort by, append ' desc' for descending",
    )


class VisualizationSuggestion(BaseModel):
    """Suggested visualization for query results."""

    widget_type: Literal["kpi", "line_chart", "bar_chart", "area_chart", "table"] = (
        Field(description="Recommended widget type")
    )
    orientation: Literal["horizontal", "vertical"] | None = Field(
        default=None,
        description="Chart orientation (for bar charts)",
    )
    format: dict | None = Field(
        default=None,
        description="Suggested format definition for values",
    )
    rationale: str = Field(
        description="Explanation of why this visualization was chosen"
    )


@dataclass
class QueryResult:
    """Result of a metric query."""

    data: list[dict]
    columns: list[str]
    row_count: int
    query_time_ms: float
    visualization: VisualizationSuggestion | None = None


# ============================================================================
# Warehouse Access (lazy initialization)
# ============================================================================

_org_warehouse = None


def _get_org_warehouse():
    """Get or create the org warehouse singleton."""
    global _org_warehouse
    if _org_warehouse is None:
        from warehouse import get_org_warehouse

        _org_warehouse = get_org_warehouse()
    return _org_warehouse


# ============================================================================
# List Functions
# ============================================================================


async def list_metrics(org_id: str) -> list[dict]:
    """List all available metrics in the organization.

    Args:
        org_id: Organization ID

    Returns:
        List of metric info dicts with name, type, description

    Raises:
        ValueError: If failed to load manifest
    """
    org_warehouse = _get_org_warehouse()
    engine, manifest = org_warehouse.get_engine(org_id)

    metrics = []
    for metric in manifest.metrics:
        metrics.append(
            {
                "name": metric.name,
                "type": (
                    metric.type.value if hasattr(metric.type, "value") else str(metric.type)
                ),
                "description": metric.description or "",
            }
        )

    return metrics


async def list_dimensions(org_id: str) -> list[dict]:
    """List all available dimensions for grouping.

    Args:
        org_id: Organization ID

    Returns:
        List of dimension info dicts with name

    Raises:
        ValueError: If failed to load manifest
    """
    org_warehouse = _get_org_warehouse()
    engine, manifest = org_warehouse.get_engine(org_id)

    dimensions = set()
    for model in manifest.semantic_models:
        for dim in model.dimensions or []:
            dimensions.add(dim.name)

    return [{"name": name} for name in sorted(dimensions)]


async def explain_metric(org_id: str, metric_name: str) -> dict:
    """Get detailed information about a metric's definition.

    Args:
        org_id: Organization ID
        metric_name: Name of the metric to explain

    Returns:
        Dict with metric details (name, type, description, measure/expression)

    Raises:
        ValueError: If metric not found
    """
    org_warehouse = _get_org_warehouse()
    engine, manifest = org_warehouse.get_engine(org_id)

    for metric in manifest.metrics:
        if metric.name == metric_name:
            result = {
                "name": metric.name,
                "type": (
                    metric.type.value if hasattr(metric.type, "value") else str(metric.type)
                ),
                "description": metric.description or "No description",
            }

            # Add type-specific details
            if metric.type_params:
                if hasattr(metric.type_params, "measure"):
                    result["measure"] = str(metric.type_params.measure)
                if hasattr(metric.type_params, "expr"):
                    result["expression"] = metric.type_params.expr
                if hasattr(metric.type_params, "metrics"):
                    result["input_metrics"] = [
                        str(m) for m in (metric.type_params.metrics or [])
                    ]

            return result

    raise ValueError(f"Metric '{metric_name}' not found")


# ============================================================================
# Query Execution
# ============================================================================

# High cardinality threshold for suggesting table visualization
HIGH_CARDINALITY_THRESHOLD = 20


async def query_metrics(
    org_id: str,
    params: QueryParams,
    include_visualization: bool = False,
) -> QueryResult:
    """Execute a metric query against the org's warehouse.

    Args:
        org_id: Organization to query
        params: Query parameters
        include_visualization: If True, include visualization suggestion

    Returns:
        QueryResult with data and optional visualization suggestion

    Raises:
        ValueError: If failed to initialize query engine
    """
    import time

    from metricflow.engine.metricflow_engine import MetricFlowQueryRequest

    org_warehouse = _get_org_warehouse()
    engine, manifest = org_warehouse.get_engine(org_id)

    # Validate warehouse client is configured
    org_warehouse.get_client(org_id)

    # Parse/default dates - MetricFlow needs datetime objects
    start_date = params.start_date
    end_date = params.end_date

    # Default to last 30 days if no dates specified
    if not start_date and not end_date:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
    elif start_date and not end_date:
        end_date = datetime.now().date()
    elif end_date and not start_date:
        start_date = end_date - timedelta(days=30)

    # Convert date to datetime for MetricFlow (expects datetime objects)
    if isinstance(start_date, date) and not isinstance(start_date, datetime):
        start_date = datetime.combine(start_date, datetime.min.time())
    if isinstance(end_date, date) and not isinstance(end_date, datetime):
        end_date = datetime.combine(end_date, datetime.max.time())

    # Build group_by list
    group_by = []
    if params.grain:
        group_by.append(f"metric_time__{params.grain}")
    if params.dimensions:
        group_by.extend(params.dimensions)

    # Build order_by list
    order_by = []
    if params.order_by:
        order_by.append(params.order_by)

    # Create the query request
    request = MetricFlowQueryRequest.create_with_random_request_id(
        metric_names=params.metrics,
        group_by_names=group_by if group_by else None,
        limit=params.limit,
        order_by_names=order_by if order_by else None,
        time_constraint_start=start_date,
        time_constraint_end=end_date,
    )

    # Execute the query in thread pool
    # 1. Use MetricFlow to generate SQL via explain()
    # 2. Execute the SQL using the warehouse client
    start_time = time.time()

    # Get the warehouse client for query execution
    client = org_warehouse.get_client(org_id)

    def run_query():
        # Generate SQL via MetricFlow
        explain_result = engine.explain(request)
        sql = explain_result.sql_statement.sql

        # Execute via warehouse client (BigQuery or DuckDB)
        data = client.query(sql)
        return data

    rows = _query_executor.submit(run_query).result(timeout=60)

    query_time_ms = (time.time() - start_time) * 1000

    # Extract columns from first row if data exists
    columns = list(rows[0].keys()) if rows else []

    result = QueryResult(
        data=rows,
        columns=columns,
        row_count=len(rows),
        query_time_ms=query_time_ms,
    )

    # Add visualization suggestion if requested
    if include_visualization:
        result.visualization = suggest_visualization(params, result)

    return result


# ============================================================================
# Visualization Suggestion
# ============================================================================


def suggest_visualization(
    params: QueryParams,
    result: QueryResult,
) -> VisualizationSuggestion:
    """Determine best visualization type based on query structure.

    Rules:
    - Single metric, no dimensions, no grain → KPI
    - Single metric with grain → Line chart
    - Single metric with 1 categorical dimension → Bar chart
    - Multiple metrics with grain → Line chart (multi-series)
    - High cardinality dimensions → Table

    Args:
        params: Original query parameters
        result: Query result data

    Returns:
        VisualizationSuggestion with widget_type and rationale
    """
    num_metrics = len(params.metrics)
    has_grain = params.grain is not None
    has_dimensions = params.dimensions is not None and len(params.dimensions) > 0
    num_dimensions = len(params.dimensions) if params.dimensions else 0
    row_count = result.row_count

    # High cardinality → Table
    if row_count > HIGH_CARDINALITY_THRESHOLD:
        return VisualizationSuggestion(
            widget_type="table",
            rationale=f"High cardinality ({row_count} rows) - table provides best overview",
        )

    # Single metric, no dimensions, no grain → KPI
    if num_metrics == 1 and not has_grain and not has_dimensions:
        return VisualizationSuggestion(
            widget_type="kpi",
            rationale="Single metric without time or dimension grouping - KPI card shows the value clearly",
        )

    # With grain (time series) → Line chart
    if has_grain:
        if num_metrics > 1:
            rationale = f"Multiple metrics ({num_metrics}) over time - line chart shows trends"
        else:
            rationale = "Single metric over time - line chart shows the trend"
        return VisualizationSuggestion(
            widget_type="line_chart",
            rationale=rationale,
        )

    # Single dimension without grain → Bar chart
    if has_dimensions and num_dimensions == 1 and not has_grain:
        return VisualizationSuggestion(
            widget_type="bar_chart",
            orientation="horizontal" if row_count > 5 else "vertical",
            rationale=f"Single dimension grouping ({params.dimensions[0]}) - bar chart compares categories",
        )

    # Multiple dimensions → Table
    if num_dimensions > 1:
        return VisualizationSuggestion(
            widget_type="table",
            rationale=f"Multiple dimensions ({num_dimensions}) - table shows the breakdown",
        )

    # Default fallback → Table
    return VisualizationSuggestion(
        widget_type="table",
        rationale="Complex query structure - table provides full data visibility",
    )
