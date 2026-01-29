"""Metricly MCP Server - Remote MCP server with Google OAuth authentication.

This server exposes Metricly's metric query and dashboard capabilities
via the Model Context Protocol (MCP), allowing Claude.ai and other
MCP-compatible clients to interact with your business metrics.

Usage:
    # Run the MCP server
    python mcp_server.py

    # Or with uvicorn for production
    uvicorn mcp_server:app --host 0.0.0.0 --port 8080

Configuration:
    Environment variables:
    - MCP_OAUTH_CLIENT_ID: Google OAuth Client ID
    - MCP_OAUTH_CLIENT_SECRET: Google OAuth Client Secret
    - MCP_SERVER_BASE_URL: Base URL for the MCP server

Claude.ai Integration:
    1. Deploy this server (e.g., to Cloud Run)
    2. In Claude.ai, go to Settings → Integrations → Add MCP Server
    3. Enter the server URL: https://your-server.com/mcp
    4. OAuth will authenticate you via Google
    5. Start asking questions about your metrics!
"""

import logging
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

from fastmcp import FastMCP, Context
from fastmcp.server.dependencies import CurrentContext
from fastmcp.server.middleware import Middleware, MiddlewareContext, CallNext
from fastmcp.server.auth.providers.google import GoogleProvider
from fastmcp.exceptions import ToolError
from pydantic import BaseModel, Field

from auth import _init_firebase
from settings import get_settings
from services.auth import UserContext, get_user_by_email
import services.dashboards as dashboard_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Thread pool for running sync queries
query_executor = ThreadPoolExecutor(max_workers=4)




# ============================================================================
# Authentication Middleware
# ============================================================================

class OrgContextMiddleware(Middleware):
    """Middleware to look up org context for authenticated OAuth user."""

    async def on_call_tool(
        self,
        context: MiddlewareContext,
        call_next: CallNext,
    ):
        """Look up user's org context and inject into tool context."""
        # Get authenticated user info from OAuth (provided by GoogleProvider)
        if not context.fastmcp_context:
            raise ToolError("Authentication required: no MCP context")

        # Get user info from OAuth authentication state
        # GoogleProvider stores access token info in request state
        try:
            from fastmcp.server.dependencies import get_access_token
            access_token = get_access_token()
        except LookupError:
            raise ToolError("Authentication required: please authenticate via OAuth")

        if not access_token:
            raise ToolError("Authentication required: no access token")

        # Get user email from Google's userinfo endpoint
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            if resp.status_code != 200:
                raise ToolError(f"Failed to get user info from Google: {resp.text}")
            user_info = resp.json()

        email = user_info.get("email")
        if not email:
            raise ToolError("OAuth authentication missing email scope")

        try:
            user = get_user_by_email(email)
        except ValueError as e:
            raise ToolError(f"Access denied: {e}")

        # Store user context in state for tools to access (async in FastMCP 3.0)
        await context.fastmcp_context.set_state("user", user)

        return await call_next(context)


# ============================================================================
# Org Warehouse (lazy initialization)
# ============================================================================

_org_warehouse = None


def get_org_warehouse():
    """Get or create the org warehouse singleton."""
    global _org_warehouse
    if _org_warehouse is None:
        from main import OrgWarehouse
        _org_warehouse = OrgWarehouse()
    return _org_warehouse


# ============================================================================
# MCP Server Setup
# ============================================================================

# Initialize Firebase before creating the server
_init_firebase()

# Get OAuth settings
settings = get_settings()

# Configure Google OAuth for Claude.ai integration
# OAuth is optional - if not configured, server runs without auth (dev mode)
auth_provider = None
if settings.mcp_oauth_client_id and settings.mcp_oauth_client_secret:
    logger.info("Configuring Google OAuth for MCP server")
    auth_provider = GoogleProvider(
        client_id=settings.mcp_oauth_client_id,
        client_secret=settings.mcp_oauth_client_secret,
        base_url=f"{settings.mcp_server_base_url}/mcp",
        # Required scopes for user identification
        required_scopes=[
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
        ],
        # Allow Claude.ai's callback URL
        allowed_client_redirect_uris=[
            "https://claude.ai/api/mcp/auth_callback",
        ],
    )
else:
    logger.warning("MCP OAuth not configured - running without authentication")

mcp = FastMCP(
    "Metricly",
    instructions="""You have access to Metricly, a business intelligence platform.

Use these tools to:
- Query business metrics (revenue, users, churn, etc.)
- List available metrics and dimensions
- View dashboard configurations

When answering questions about metrics:
1. First use list_metrics to see what's available
2. Use query_metrics to fetch actual data
3. Provide insights based on the results

Always specify date ranges when querying to get relevant data.""",
    auth=auth_provider,
)

# Add org context middleware (after OAuth authentication)
mcp.add_middleware(OrgContextMiddleware())


# ============================================================================
# Tool Parameter Models
# ============================================================================

class QueryParams(BaseModel):
    """Parameters for querying metrics."""
    metrics: list[str] = Field(description="List of metric names to query (e.g., ['total_revenue', 'order_count'])")
    dimensions: list[str] | None = Field(default=None, description="Dimensions to group by (e.g., ['customer_segment', 'region'])")
    grain: str | None = Field(default=None, description="Time granularity: 'day', 'week', 'month', 'quarter', or 'year'")
    start_date: str | None = Field(default=None, description="Start date in YYYY-MM-DD format")
    end_date: str | None = Field(default=None, description="End date in YYYY-MM-DD format")
    limit: int | None = Field(default=None, description="Maximum number of rows to return")
    order_by: str | None = Field(default=None, description="Column to sort by, append ' desc' for descending (e.g., 'total_revenue desc')")


# ============================================================================
# MCP Tools
# ============================================================================

@mcp.tool()
async def list_metrics(ctx: Context = CurrentContext()) -> list[dict]:
    """List all available metrics in the organization.

    Returns metrics with their names, types, descriptions, and definitions.
    Use this to discover what metrics are available before querying.
    """
    user: UserContext = await ctx.get_state("user")

    try:
        org_warehouse = get_org_warehouse()
        engine, manifest = org_warehouse.get_engine(user.org_id)
    except ValueError as e:
        return [{"error": f"Failed to load metrics: {e}"}]

    metrics = []
    for metric in manifest.semantic_manifest.metrics:
        metrics.append({
            "name": metric.name,
            "type": metric.type.value if hasattr(metric.type, 'value') else str(metric.type),
            "description": metric.description or "",
        })

    return metrics


@mcp.tool()
async def list_dimensions(ctx: Context = CurrentContext()) -> list[dict]:
    """List all available dimensions that can be used for grouping.

    Dimensions are attributes you can group metrics by (e.g., customer_segment, region, product_category).
    """
    user: UserContext = await ctx.get_state("user")

    try:
        org_warehouse = get_org_warehouse()
        engine, manifest = org_warehouse.get_engine(user.org_id)
    except ValueError as e:
        return [{"error": f"Failed to load dimensions: {e}"}]

    dimensions = set()
    for model in manifest.semantic_manifest.semantic_models:
        for dim in (model.dimensions or []):
            dimensions.add(dim.name)

    return [{"name": name} for name in sorted(dimensions)]


@mcp.tool()
async def query_metrics(params: QueryParams, ctx: Context = CurrentContext()) -> dict:
    """Execute a metric query and return the results.

    Use this to fetch actual data for one or more metrics. You can optionally:
    - Group by dimensions
    - Filter by time range
    - Limit results
    - Sort by a column

    Example queries:
    - Monthly revenue: metrics=['total_revenue'], grain='month', start_date='2024-01-01'
    - Revenue by region: metrics=['total_revenue'], dimensions=['region']
    - Top 10 customers: metrics=['total_revenue'], dimensions=['customer_name'], order_by='total_revenue desc', limit=10
    """
    user: UserContext = await ctx.get_state("user")

    try:
        org_warehouse = get_org_warehouse()
        engine, manifest = org_warehouse.get_engine(user.org_id)
        _client = org_warehouse.get_client(user.org_id)  # Validates client is configured
    except ValueError as e:
        return {"error": f"Failed to initialize query engine: {e}"}

    # Import MetricFlow components
    from metricflow.engine.metricflow_engine import MetricFlowQueryRequest

    # Build the query request
    try:
        # Parse dates
        start_date = None
        end_date = None
        if params.start_date:
            start_date = datetime.strptime(params.start_date, "%Y-%m-%d").date()
        if params.end_date:
            end_date = datetime.strptime(params.end_date, "%Y-%m-%d").date()

        # Default to last 30 days if no dates specified
        if not start_date and not end_date:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)
        elif start_date and not end_date:
            end_date = datetime.now().date()
        elif end_date and not start_date:
            start_date = end_date - timedelta(days=30)

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

        # Execute the query
        def run_query():
            result = engine.query(request)
            if result.exception:
                raise result.exception
            return result.df

        # Run in thread pool to avoid blocking
        df = query_executor.submit(run_query).result(timeout=60)

        # Convert to list of dicts
        rows = df.to_dict(orient="records")

        return {
            "success": True,
            "row_count": len(rows),
            "columns": list(df.columns),
            "data": rows,
        }

    except Exception as e:
        logger.error(f"Query failed: {e}")
        return {"error": str(e)}


@mcp.tool()
async def list_dashboards(ctx: Context = CurrentContext()) -> list[dict]:
    """List all dashboards accessible to the user.

    Returns dashboard titles, descriptions, and visibility (private or shared with org).
    """
    user: UserContext = await ctx.get_state("user")

    try:
        result = await dashboard_service.list_dashboards(user)
        dashboards = []

        for d in result.personal:
            dashboards.append({
                "id": d.id,
                "title": d.title,
                "description": d.description,
                "visibility": "private",
                "owner": d.owner,
            })

        for d in result.team:
            dashboards.append({
                "id": d.id,
                "title": d.title,
                "description": d.description,
                "visibility": "org",
                "owner": d.owner,
            })

        return dashboards
    except Exception as e:
        return [{"error": f"Failed to list dashboards: {e}"}]


@mcp.tool()
async def get_dashboard(dashboard_id: str, ctx: Context = CurrentContext()) -> dict:
    """Get detailed information about a specific dashboard.

    Returns the full dashboard configuration including pages, sections, and widgets.
    """
    user: UserContext = await ctx.get_state("user")

    try:
        dashboard = await dashboard_service.get_dashboard(user, dashboard_id)
        return dashboard.model_dump()
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to get dashboard: {e}"}


@mcp.tool()
async def explain_metric(metric_name: str, ctx: Context = CurrentContext()) -> dict:
    """Get detailed information about how a specific metric is calculated.

    Returns the metric definition including its type, formula, and underlying measures.
    """
    user: UserContext = await ctx.get_state("user")

    try:
        org_warehouse = get_org_warehouse()
        engine, manifest = org_warehouse.get_engine(user.org_id)
    except ValueError as e:
        return {"error": f"Failed to load metric: {e}"}

    # Find the metric in the manifest
    for metric in manifest.semantic_manifest.metrics:
        if metric.name == metric_name:
            result = {
                "name": metric.name,
                "type": metric.type.value if hasattr(metric.type, 'value') else str(metric.type),
                "description": metric.description or "No description",
            }

            # Add type-specific details
            if metric.type_params:
                if hasattr(metric.type_params, 'measure'):
                    result["measure"] = str(metric.type_params.measure)
                if hasattr(metric.type_params, 'expr'):
                    result["expression"] = metric.type_params.expr
                if hasattr(metric.type_params, 'metrics'):
                    result["input_metrics"] = [str(m) for m in (metric.type_params.metrics or [])]

            return result

    return {"error": f"Metric '{metric_name}' not found"}


@mcp.tool()
async def create_dashboard(
    title: str,
    description: str | None = None,
    visibility: str = "private",
    ctx: Context = CurrentContext(),
) -> dict:
    """Create a new dashboard.

    Args:
        title: Dashboard title
        description: Optional description
        visibility: "private" (only you) or "org" (shared with organization)

    Returns the created dashboard with its generated ID.
    """
    user: UserContext = await ctx.get_state("user")

    if visibility not in ("private", "org"):
        return {"error": f"Invalid visibility: {visibility}. Must be 'private' or 'org'"}

    try:
        dashboard = await dashboard_service.create_dashboard(
            user,
            title=title,
            description=description,
            visibility=visibility,
        )
        return {
            "success": True,
            "dashboard": dashboard.model_dump(),
        }
    except Exception as e:
        return {"error": f"Failed to create dashboard: {e}"}


@mcp.tool()
async def update_dashboard(
    dashboard_id: str,
    title: str | None = None,
    description: str | None = None,
    visibility: str | None = None,
    ctx: Context = CurrentContext(),
) -> dict:
    """Update an existing dashboard.

    Args:
        dashboard_id: ID of the dashboard to update
        title: New title (optional)
        description: New description (optional)
        visibility: New visibility - "private" or "org" (optional)

    Only fields that are provided will be updated.
    You must be the owner of the dashboard to update it.
    """
    user: UserContext = await ctx.get_state("user")

    updates = {}
    if title is not None:
        updates["title"] = title
    if description is not None:
        updates["description"] = description
    if visibility is not None:
        if visibility not in ("private", "org"):
            return {"error": f"Invalid visibility: {visibility}. Must be 'private' or 'org'"}
        updates["visibility"] = visibility

    if not updates:
        return {"error": "No updates provided"}

    try:
        dashboard = await dashboard_service.update_dashboard(user, dashboard_id, updates)
        return {
            "success": True,
            "dashboard": dashboard.model_dump(),
        }
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to update dashboard: {e}"}


@mcp.tool()
async def delete_dashboard(dashboard_id: str, ctx: Context = CurrentContext()) -> dict:
    """Delete a dashboard.

    Args:
        dashboard_id: ID of the dashboard to delete

    You must be the owner of the dashboard to delete it.
    This action cannot be undone.
    """
    user: UserContext = await ctx.get_state("user")

    try:
        await dashboard_service.delete_dashboard(user, dashboard_id)
        return {"success": True, "message": f"Dashboard '{dashboard_id}' deleted"}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to delete dashboard: {e}"}


# ============================================================================
# Manifest Tools
# ============================================================================

import services.manifest as manifest_service


@mcp.tool()
async def get_manifest_status(ctx: Context = CurrentContext()) -> dict:
    """Get status information about the organization's semantic manifest.

    Returns manifest metadata including metric/model/dimension counts.
    """
    user: UserContext = await ctx.get_state("user")

    try:
        status = await manifest_service.get_manifest_status(user)
        return {
            "org_id": status.org_id,
            "project_name": status.project_name,
            "metric_count": status.metric_count,
            "model_count": status.model_count,
            "dimension_count": status.dimension_count,
            "last_updated": status.last_updated,
        }
    except Exception as e:
        return {"error": f"Failed to get manifest status: {e}"}


@mcp.tool()
async def list_semantic_models(ctx: Context = CurrentContext()) -> list[dict]:
    """List all semantic models in the organization.

    Returns models with their names, descriptions, measures, and dimensions.
    """
    user: UserContext = await ctx.get_state("user")

    try:
        return await manifest_service.list_semantic_models(user)
    except Exception as e:
        return [{"error": f"Failed to list semantic models: {e}"}]


@mcp.tool()
async def get_semantic_model(name: str, ctx: Context = CurrentContext()) -> dict:
    """Get detailed information about a semantic model.

    Args:
        name: Name of the semantic model
    """
    user: UserContext = await ctx.get_state("user")

    try:
        return await manifest_service.get_semantic_model(user, name)
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to get semantic model: {e}"}


@mcp.tool()
async def create_semantic_model(model_data: dict, ctx: Context = CurrentContext()) -> dict:
    """Create a new semantic model.

    Args:
        model_data: Semantic model definition with name, measures, dimensions

    Requires admin or owner role.
    """
    user: UserContext = await ctx.get_state("user")

    try:
        result = await manifest_service.create_semantic_model(user, model_data)
        return {"success": True, "model": result}
    except PermissionError as e:
        return {"error": str(e)}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to create semantic model: {e}"}


@mcp.tool()
async def update_semantic_model(
    name: str,
    updates: dict,
    ctx: Context = CurrentContext(),
) -> dict:
    """Update an existing semantic model.

    Args:
        name: Name of the model to update
        updates: Fields to update

    Requires admin or owner role.
    """
    user: UserContext = await ctx.get_state("user")

    try:
        result = await manifest_service.update_semantic_model(user, name, updates)
        return {"success": True, "model": result}
    except PermissionError as e:
        return {"error": str(e)}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to update semantic model: {e}"}


@mcp.tool()
async def delete_semantic_model(name: str, ctx: Context = CurrentContext()) -> dict:
    """Delete a semantic model.

    Args:
        name: Name of the model to delete

    Requires admin or owner role. This action cannot be undone.
    """
    user: UserContext = await ctx.get_state("user")

    try:
        await manifest_service.delete_semantic_model(user, name)
        return {"success": True, "message": f"Semantic model '{name}' deleted"}
    except PermissionError as e:
        return {"error": str(e)}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to delete semantic model: {e}"}


@mcp.tool()
async def create_metric(metric_data: dict, ctx: Context = CurrentContext()) -> dict:
    """Create a new metric.

    Args:
        metric_data: Metric definition with name, type, type_params

    Requires admin or owner role.
    """
    user: UserContext = await ctx.get_state("user")

    try:
        result = await manifest_service.create_metric(user, metric_data)
        return {"success": True, "metric": result}
    except PermissionError as e:
        return {"error": str(e)}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to create metric: {e}"}


@mcp.tool()
async def update_metric(
    name: str,
    updates: dict,
    ctx: Context = CurrentContext(),
) -> dict:
    """Update an existing metric.

    Args:
        name: Name of the metric to update
        updates: Fields to update

    Requires admin or owner role.
    """
    user: UserContext = await ctx.get_state("user")

    try:
        result = await manifest_service.update_metric(user, name, updates)
        return {"success": True, "metric": result}
    except PermissionError as e:
        return {"error": str(e)}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to update metric: {e}"}


@mcp.tool()
async def delete_metric(name: str, ctx: Context = CurrentContext()) -> dict:
    """Delete a metric.

    Args:
        name: Name of the metric to delete

    Requires admin or owner role. This action cannot be undone.
    """
    user: UserContext = await ctx.get_state("user")

    try:
        await manifest_service.delete_metric(user, name)
        return {"success": True, "message": f"Metric '{name}' deleted"}
    except PermissionError as e:
        return {"error": str(e)}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to delete metric: {e}"}


@mcp.tool()
async def import_manifest(
    manifest_data: dict,
    force: bool = False,
    ctx: Context = CurrentContext(),
) -> dict:
    """Import a semantic manifest with fork detection.

    Args:
        manifest_data: Full manifest with metrics and semantic_models
        force: If True, overwrite forked (modified) metrics. If False, fail on conflicts.

    Requires admin or owner role.

    Forked metrics are ones that were imported and then modified by users.
    Without --force, import will fail listing the conflicting items.
    """
    user: UserContext = await ctx.get_state("user")

    try:
        result = await manifest_service.import_manifest(user, manifest_data, force=force)
        return {
            "success": True,
            "imported_metrics": result.imported_metrics,
            "imported_models": result.imported_models,
            "skipped_metrics": result.skipped_metrics,
            "skipped_models": result.skipped_models,
            "conflicts": [
                {"name": c.name, "type": c.type, "reason": c.reason}
                for c in result.conflicts
            ],
            "orphaned": result.orphaned,
        }
    except PermissionError as e:
        return {"error": str(e)}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to import manifest: {e}"}


@mcp.tool()
async def preview_metric(
    metric_data: dict,
    sample_query: dict | None = None,
    ctx: Context = CurrentContext(),
) -> dict:
    """Preview a metric's query results before saving.

    Args:
        metric_data: Metric definition to preview
        sample_query: Optional query params (start_date, end_date, grain, limit).
                      Defaults to last 7 days, daily grain, limit 5.

    Returns sample query results or validation error.
    """
    user: UserContext = await ctx.get_state("user")

    try:
        return await manifest_service.preview_metric(user, metric_data, sample_query)
    except Exception as e:
        return {"error": f"Failed to preview metric: {e}"}


# ============================================================================
# Server Entry Point
# ============================================================================

# Create the ASGI app for deployment
# Use path="/" since we mount this under /mcp in main.py
app = mcp.http_app(path="/")

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting Metricly MCP Server on port {port}")

    # Run with HTTP transport for remote connections
    uvicorn.run(app, host="0.0.0.0", port=port)
