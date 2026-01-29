"""Dashboard services - CRUD operations and widget management.

Provides typed dashboard operations for MCP, CLI, and chat consumers.
Wraps storage.py with Pydantic validation and permission checks.
"""

from dataclasses import dataclass
from typing import Literal, Optional
import uuid

from generated.dashboard_types import (
    DashboardDefinition,
    PageDefinition,
    SectionDefinition,
    WidgetDefinition,
)
from services.auth import UserContext, require_role

import storage


# ============================================================================
# Types
# ============================================================================


@dataclass
class DashboardSummary:
    """Summary info for dashboard listing."""

    id: str
    title: str
    description: str | None
    owner: str
    visibility: Literal["private", "org"]
    created_at: str
    updated_at: str


@dataclass
class DashboardList:
    """Result of list_dashboards."""

    personal: list[DashboardSummary]
    team: list[DashboardSummary]


# ============================================================================
# CRUD Operations
# ============================================================================


async def list_dashboards(user: UserContext) -> DashboardList:
    """List dashboards visible to user.

    Args:
        user: Authenticated user context

    Returns:
        DashboardList with personal and team sections
    """
    result = storage.list_dashboards(user.org_id, user.uid)

    def to_summary(d: dict) -> DashboardSummary:
        return DashboardSummary(
            id=d.get("id", ""),
            title=d.get("title", "Untitled"),
            description=d.get("description"),
            owner=d.get("owner", ""),
            visibility=d.get("visibility", "private"),
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
        )

    return DashboardList(
        personal=[to_summary(d) for d in result.get("personal", [])],
        team=[to_summary(d) for d in result.get("team", [])],
    )


async def get_dashboard(user: UserContext, dashboard_id: str) -> DashboardDefinition:
    """Get a dashboard by ID.

    Args:
        user: Authenticated user context
        dashboard_id: Dashboard ID

    Returns:
        Validated DashboardDefinition

    Raises:
        ValueError: If dashboard not found or access denied
    """
    data = storage.get_dashboard(user.org_id, dashboard_id, user.uid)

    if not data:
        raise ValueError(f"Dashboard '{dashboard_id}' not found or access denied")

    return DashboardDefinition.model_validate(data)


async def create_dashboard(
    user: UserContext,
    title: str,
    description: str | None = None,
    visibility: Literal["private", "org"] = "private",
    pages: list[dict] | None = None,
    controls: dict | None = None,
) -> DashboardDefinition:
    """Create a new dashboard.

    Args:
        user: Authenticated user context
        title: Dashboard title
        description: Optional description
        visibility: "private" or "org"
        pages: Optional initial pages (defaults to empty page)
        controls: Optional dashboard controls config

    Returns:
        Created DashboardDefinition
    """
    # Build default controls if not provided
    if controls is None:
        controls = {
            "date_range": {"mode": "relative", "preset": "last_30_days"},
            "grain": "month",
            "comparison": "none",
        }

    # Build default page if not provided
    if pages is None:
        pages = [
            {
                "id": str(uuid.uuid4()),
                "title": "Overview",
                "sections": [],
            }
        ]

    dashboard_data = {
        "title": title,
        "description": description,
        "visibility": visibility,
        "controls": controls,
        "pages": pages,
    }

    result = storage.create_dashboard(user.org_id, user.uid, dashboard_data)
    return DashboardDefinition.model_validate(result)


async def create_dashboard_from_definition(
    user: UserContext,
    definition: dict,
) -> DashboardDefinition:
    """Create a dashboard from a full definition (e.g., from YAML file).

    Args:
        user: Authenticated user context
        definition: Dashboard definition dict

    Returns:
        Created DashboardDefinition
    """
    # Remove fields that will be set by storage
    definition.pop("id", None)
    definition.pop("owner", None)
    definition.pop("created_at", None)
    definition.pop("updated_at", None)
    definition.pop("created_by", None)

    # Validate before saving
    DashboardDefinition.model_validate({
        **definition,
        "id": "temp",
        "owner": user.uid,
        "created_at": "2000-01-01T00:00:00Z",
        "updated_at": "2000-01-01T00:00:00Z",
        "created_by": user.uid,
    })

    result = storage.create_dashboard(user.org_id, user.uid, definition)
    return DashboardDefinition.model_validate(result)


async def update_dashboard(
    user: UserContext,
    dashboard_id: str,
    updates: dict,
) -> DashboardDefinition:
    """Update a dashboard.

    Args:
        user: Authenticated user context
        dashboard_id: Dashboard ID
        updates: Fields to update

    Returns:
        Updated DashboardDefinition

    Raises:
        ValueError: If dashboard not found or user is not owner
        PermissionError: If user lacks permission
    """
    result = storage.update_dashboard(user.org_id, dashboard_id, user.uid, updates)

    if not result:
        raise ValueError(
            f"Dashboard '{dashboard_id}' not found or you are not the owner"
        )

    return DashboardDefinition.model_validate(result)


async def delete_dashboard(user: UserContext, dashboard_id: str) -> bool:
    """Delete a dashboard.

    Args:
        user: Authenticated user context
        dashboard_id: Dashboard ID

    Returns:
        True if deleted

    Raises:
        ValueError: If dashboard not found or user is not owner
    """
    success = storage.delete_dashboard(user.org_id, dashboard_id, user.uid)

    if not success:
        raise ValueError(
            f"Dashboard '{dashboard_id}' not found or you are not the owner"
        )

    return True


# ============================================================================
# Widget Operations
# ============================================================================


async def add_widget(
    user: UserContext,
    dashboard_id: str,
    widget: dict,
    page_index: int = 0,
    section_index: int = 0,
) -> DashboardDefinition:
    """Add a widget to a dashboard.

    Args:
        user: Authenticated user context
        dashboard_id: Dashboard ID
        widget: Widget definition dict
        page_index: Index of page to add to
        section_index: Index of section within page

    Returns:
        Updated DashboardDefinition

    Raises:
        ValueError: If dashboard/page/section not found or validation fails
    """
    # Get current dashboard
    dashboard = await get_dashboard(user, dashboard_id)

    # Validate widget
    if "id" not in widget:
        widget["id"] = str(uuid.uuid4())
    validated_widget = WidgetDefinition.model_validate(widget)

    # Get pages as mutable list
    pages = [p.model_dump() for p in dashboard.pages]

    # Validate indices
    if page_index < 0 or page_index >= len(pages):
        raise ValueError(f"Page index {page_index} out of range (0-{len(pages)-1})")

    page = pages[page_index]
    sections = page.get("sections", [])

    if section_index < 0 or section_index >= len(sections):
        # Create section if it doesn't exist and index is 0
        if section_index == 0 and len(sections) == 0:
            sections.append({"widgets": []})
        else:
            raise ValueError(
                f"Section index {section_index} out of range (0-{len(sections)-1})"
            )

    # Add widget to section
    sections[section_index]["widgets"].append(validated_widget.model_dump())
    pages[page_index]["sections"] = sections

    # Update dashboard
    return await update_dashboard(user, dashboard_id, {"pages": pages})


async def remove_widget(
    user: UserContext,
    dashboard_id: str,
    page_index: int,
    section_index: int,
    widget_index: int,
) -> DashboardDefinition:
    """Remove a widget from a dashboard.

    Args:
        user: Authenticated user context
        dashboard_id: Dashboard ID
        page_index: Index of page
        section_index: Index of section within page
        widget_index: Index of widget within section

    Returns:
        Updated DashboardDefinition

    Raises:
        ValueError: If indices are invalid
    """
    # Get current dashboard
    dashboard = await get_dashboard(user, dashboard_id)

    # Get pages as mutable list
    pages = [p.model_dump() for p in dashboard.pages]

    # Validate indices
    if page_index < 0 or page_index >= len(pages):
        raise ValueError(f"Page index {page_index} out of range")

    sections = pages[page_index].get("sections", [])
    if section_index < 0 or section_index >= len(sections):
        raise ValueError(f"Section index {section_index} out of range")

    widgets = sections[section_index].get("widgets", [])
    if widget_index < 0 or widget_index >= len(widgets):
        raise ValueError(f"Widget index {widget_index} out of range")

    # Remove widget
    widgets.pop(widget_index)
    pages[page_index]["sections"][section_index]["widgets"] = widgets

    # Update dashboard
    return await update_dashboard(user, dashboard_id, {"pages": pages})


async def update_widget(
    user: UserContext,
    dashboard_id: str,
    page_index: int,
    section_index: int,
    widget_index: int,
    updates: dict,
) -> DashboardDefinition:
    """Update a specific widget in a dashboard.

    Args:
        user: Authenticated user context
        dashboard_id: Dashboard ID
        page_index: Index of page
        section_index: Index of section within page
        widget_index: Index of widget within section
        updates: Fields to update on the widget

    Returns:
        Updated DashboardDefinition

    Raises:
        ValueError: If indices are invalid or validation fails
    """
    # Get current dashboard
    dashboard = await get_dashboard(user, dashboard_id)

    # Get pages as mutable list
    pages = [p.model_dump() for p in dashboard.pages]

    # Validate indices
    if page_index < 0 or page_index >= len(pages):
        raise ValueError(f"Page index {page_index} out of range")

    sections = pages[page_index].get("sections", [])
    if section_index < 0 or section_index >= len(sections):
        raise ValueError(f"Section index {section_index} out of range")

    widgets = sections[section_index].get("widgets", [])
    if widget_index < 0 or widget_index >= len(widgets):
        raise ValueError(f"Widget index {widget_index} out of range")

    # Update widget
    current_widget = widgets[widget_index]
    updated_widget = {**current_widget, **updates}

    # Validate updated widget
    validated = WidgetDefinition.model_validate(updated_widget)
    widgets[widget_index] = validated.model_dump()
    pages[page_index]["sections"][section_index]["widgets"] = widgets

    # Update dashboard
    return await update_dashboard(user, dashboard_id, {"pages": pages})


async def reorder_widgets(
    user: UserContext,
    dashboard_id: str,
    page_index: int,
    section_index: int,
    widget_ids: list[str],
) -> DashboardDefinition:
    """Reorder widgets within a section.

    Args:
        user: Authenticated user context
        dashboard_id: Dashboard ID
        page_index: Index of page
        section_index: Index of section within page
        widget_ids: New order of widget IDs

    Returns:
        Updated DashboardDefinition

    Raises:
        ValueError: If indices are invalid or widget IDs don't match
    """
    # Get current dashboard
    dashboard = await get_dashboard(user, dashboard_id)

    # Get pages as mutable list
    pages = [p.model_dump() for p in dashboard.pages]

    # Validate indices
    if page_index < 0 or page_index >= len(pages):
        raise ValueError(f"Page index {page_index} out of range")

    sections = pages[page_index].get("sections", [])
    if section_index < 0 or section_index >= len(sections):
        raise ValueError(f"Section index {section_index} out of range")

    widgets = sections[section_index].get("widgets", [])
    widget_map = {w["id"]: w for w in widgets}

    # Validate widget IDs
    current_ids = set(widget_map.keys())
    new_ids = set(widget_ids)
    if current_ids != new_ids:
        raise ValueError("Widget IDs don't match current widgets")

    # Reorder
    reordered = [widget_map[wid] for wid in widget_ids]
    pages[page_index]["sections"][section_index]["widgets"] = reordered

    # Update dashboard
    return await update_dashboard(user, dashboard_id, {"pages": pages})
