"""Cost management mixin for providers."""

from __future__ import annotations

from typing import Any

FIELDS_COSTS_BASE = {
    "service": {
        "label": "Service",
        "description": "Service",
        "format": "str",
    },
    "cost": {
        "label": "Cost",
        "description": "Cost",
        "format": "str",
    },
}

class CostMixin:
    """Mixin for managing service costs."""

    def is_cost_implemented(self, service_name: str) -> bool:
        """Check if cost property for a service is implemented."""
        cost_property = f'cost_{service_name}'
        return hasattr(self, cost_property)

    def get_cost(self, service_name: str) -> Any:
        """Get cost for a service."""
        cost_property = f'cost_{service_name}'
        cost = getattr(self, cost_property, 0)
        if cost in ('free', 0):
            return 'free'
        return cost

    def calculate_cost(self, service_name: str, **data: Any) -> Any:
        """Calculate cost for a service from data."""
        calculate_method = f'calculate_cost_{service_name}'
        method = getattr(self, calculate_method)
        cost = method(**data)
        if cost in ('free', 0):
            return 'free'
        return cost

    def get_costs_services(self) -> dict[str, Any]:
        """Get costs for all services."""
        services = getattr(self, 'services', [])
        return {service: self.get_cost(service) for service in services}

    @property
    def costs_services(self) -> dict[str, Any]:
        """Get costs for all services."""
        return self.get_costs_services()
