"""Service analysis tools for BPA API.

This module provides MCP tools for analyzing BPA services.
Note: The BPA API is service-centric and does not support cross-object
relationship queries. Analysis is limited to service-level data.

Tools:
    analyze_service: Analyze a BPA service with AI-optimized output
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp.exceptions import ToolError

from mcp_eregistrations_bpa.bpa_client import BPAClient
from mcp_eregistrations_bpa.bpa_client.errors import (
    BPAClientError,
    BPANotFoundError,
    translate_error,
)

__all__ = [
    "analyze_service",
    "register_analysis_tools",
]


def _transform_summary(item: dict[str, Any]) -> dict[str, Any]:
    """Transform an item to a summary with id/key and name."""
    return {
        "id": item.get("id"),
        "key": item.get("key"),
        "name": item.get("name"),
    }


def _calculate_complexity_score(
    registration_count: int,
    field_count: int,
    determinant_count: int,
) -> str:
    """Calculate service complexity score.

    Scoring criteria:
    - low: ≤5 registrations, ≤20 fields, ≤5 determinants
    - medium: ≤15 registrations, ≤50 fields, ≤20 determinants
    - high: Exceeds medium thresholds

    Args:
        registration_count: Number of registrations in the service.
        field_count: Number of fields in the service.
        determinant_count: Number of determinants in the service.

    Returns:
        Complexity level: "low", "medium", or "high".
    """
    if registration_count <= 5 and field_count <= 20 and determinant_count <= 5:
        return "low"
    elif registration_count <= 15 and field_count <= 50 and determinant_count <= 20:
        return "medium"
    else:
        return "high"


def _build_service_overview(
    service_data: dict[str, Any],
    registrations: list[dict[str, Any]],
    fields: list[dict[str, Any]],
    determinants: list[dict[str, Any]],
    forms: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build service overview with counts for AI reasoning.

    Args:
        service_data: Service metadata from API.
        registrations: List of registrations.
        fields: List of fields.
        determinants: List of determinants.
        forms: List of forms.

    Returns:
        Overview dictionary with status, counts, and complexity score.
    """
    return {
        "status": service_data.get("status", "active"),
        "total_registrations": len(registrations),
        "total_fields": len(fields),
        "total_determinants": len(determinants),
        "total_forms": len(forms),
        "complexity_score": _calculate_complexity_score(
            len(registrations), len(fields), len(determinants)
        ),
    }


def _build_fields_summary(
    fields: list[dict[str, Any]],
    max_sample_size: int = 10,
) -> dict[str, Any]:
    """Build a summarized fields object for AI consumption.

    Instead of returning all fields (which can be 1000+ items), this function
    returns a summary with:
    - total: Count of all fields
    - by_type: Breakdown of fields by type with counts
    - sample: Representative sample of up to max_sample_size fields

    Sample selection strategy:
    - Distribute samples across different field types for variety
    - If fewer fields than max_sample_size, return all fields
    - Include key, type, name for each sample field

    Args:
        fields: List of field dictionaries from BPA API.
        max_sample_size: Maximum number of fields in the sample (default: 10).

    Returns:
        Dictionary with total, by_type, and sample fields.
    """
    total = len(fields)

    # Group fields by type
    fields_by_type: dict[str, list[dict[str, Any]]] = {}
    for field in fields:
        field_type = field.get("type", "unknown")
        if field_type not in fields_by_type:
            fields_by_type[field_type] = []
        fields_by_type[field_type].append(field)

    # Build by_type counts
    by_type = {field_type: len(items) for field_type, items in fields_by_type.items()}

    # Build sample with diversity across types
    sample: list[dict[str, Any]] = []
    if total <= max_sample_size:
        # Return all fields if we have fewer than max_sample_size
        sample = [
            {
                "key": f.get("key"),
                "type": f.get("type"),
                "name": f.get("name"),
            }
            for f in fields
        ]
    else:
        # Distribute samples across types for diversity
        type_count = len(fields_by_type)
        if type_count > 0:
            # Calculate base samples per type
            samples_per_type = max(1, max_sample_size // type_count)
            remaining_slots = max_sample_size

            # Sort types by count (largest first) to prioritize common types
            sorted_types = sorted(
                fields_by_type.keys(),
                key=lambda t: len(fields_by_type[t]),
                reverse=True,
            )

            # Track how many we took from each type
            taken_from_type: dict[str, int] = {t: 0 for t in sorted_types}

            # First pass: take samples_per_type from each type
            for field_type in sorted_types:
                if remaining_slots <= 0:
                    break
                type_fields = fields_by_type[field_type]
                take_count = min(samples_per_type, len(type_fields), remaining_slots)
                for f in type_fields[:take_count]:
                    sample.append(
                        {
                            "key": f.get("key"),
                            "type": f.get("type"),
                            "name": f.get("name"),
                        }
                    )
                taken_from_type[field_type] = take_count
                remaining_slots -= take_count

            # Second pass: fill remaining slots from types with more fields
            for field_type in sorted_types:
                if remaining_slots <= 0:
                    break
                type_fields = fields_by_type[field_type]
                already_taken = taken_from_type[field_type]
                available = len(type_fields) - already_taken
                if available > 0:
                    take_more = min(available, remaining_slots)
                    for f in type_fields[already_taken : already_taken + take_more]:
                        sample.append(
                            {
                                "key": f.get("key"),
                                "type": f.get("type"),
                                "name": f.get("name"),
                            }
                        )
                    remaining_slots -= take_more

    return {
        "total": total,
        "by_type": by_type,
        "sample": sample,
    }


def _generate_insights(overview: dict[str, Any]) -> list[str]:
    """Generate actionable insights for AI reasoning.

    Args:
        overview: Service overview data.

    Returns:
        List of insight strings.
    """
    insights: list[str] = []

    # Complexity insight
    complexity = overview.get("complexity_score", "low")
    total_fields = overview.get("total_fields", 0)
    total_determinants = overview.get("total_determinants", 0)
    total_registrations = overview.get("total_registrations", 0)

    if complexity == "high":
        insights.append("Service has high complexity - consider modular restructuring")
    elif complexity == "medium":
        insights.append("Service has moderate complexity")
    else:
        insights.append("Service has low complexity - well organized")

    # Field insights
    if total_fields > 50:
        insights.append(f"Service has {total_fields} fields - review for consolidation")

    # Determinant insights
    if total_determinants > 20:
        insights.append(
            f"Service has {total_determinants} determinants - "
            "complex business rules present"
        )
    elif total_determinants == 0:
        insights.append("No determinants - all fields are always visible")

    # Registration insights
    if total_registrations > 10:
        insights.append(
            f"Service has {total_registrations} registrations - "
            "consider grouping related ones"
        )
    elif total_registrations == 0:
        insights.append("No registrations defined yet")

    return insights


async def analyze_service(service_id: str | int) -> dict[str, Any]:
    """Analyze a BPA service with AI-optimized output.

    Note: BPA API is service-centric. Cross-object relationships
    (e.g., which fields use which determinants) are not queryable.

    Args:
        service_id: The unique identifier of the service.

    Returns:
        dict with service_id, service_name, overview, registrations,
        fields_summary, determinants, insights.
    """
    try:
        async with BPAClient() as client:
            try:
                # Get service details (includes embedded registrations)
                service_data = await client.get(
                    "/service/{id}",
                    path_params={"id": service_id},
                    resource_type="service",
                    resource_id=service_id,
                )

                # Extract registrations from service response
                # Note: BPA API embeds registrations in service, no separate endpoint
                registrations = service_data.get("registrations", [])

                # Get fields using service-scoped endpoint
                fields = await client.get_list(
                    "/service/{service_id}/fields",
                    path_params={"service_id": service_id},
                    resource_type="field",
                )

                # Get determinants using service-scoped endpoint
                determinants = await client.get_list(
                    "/service/{service_id}/determinant",
                    path_params={"service_id": service_id},
                    resource_type="determinant",
                )

                # Note: /service/{id}/form endpoint doesn't exist
                # Forms are accessed via /service/{id}/applicant-form
                forms: list[dict[str, Any]] = []

                # Build AI-optimized response
                overview = _build_service_overview(
                    service_data, registrations, fields, determinants, forms
                )

                insights = _generate_insights(overview)

                # Build fields summary instead of returning all fields
                # This reduces response size from ~132KB to ~5KB for large services
                fields_summary = _build_fields_summary(fields)

                return {
                    "service_id": service_id,
                    "service_name": service_data.get("name", ""),
                    "description": service_data.get("description", ""),
                    "overview": overview,
                    "registrations": [
                        {"id": r.get("id"), "name": r.get("name")}
                        for r in registrations
                    ],
                    "fields_summary": fields_summary,
                    "determinants": [
                        {
                            "id": d.get("id"),
                            "name": d.get("name"),
                            "type": d.get("type"),
                        }
                        for d in determinants
                    ],
                    "insights": insights,
                }

            except BPANotFoundError:
                raise ToolError(
                    f"Service {service_id} not found. "
                    "Use 'service_list' to see available services."
                )
    except ToolError:
        raise
    except BPAClientError as e:
        raise translate_error(e, resource_type="service", resource_id=service_id)


def register_analysis_tools(mcp: Any) -> None:
    """Register analysis tools with the MCP server.

    Args:
        mcp: The FastMCP server instance.
    """
    mcp.tool()(analyze_service)
