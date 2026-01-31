from .check import HealthCheck


class HealthCheckRegistry:
    def __init__(self):
        self._checks: list[HealthCheck] = []

    def register(self, check: HealthCheck) -> None:
        existing_names = {c.service_name for c in self._checks}
        if check.service_name in existing_names:
            raise ValueError(f"Health check with service name '{check.service_name}' already exists")
        self._checks.append(check)

    def unregister(self, service_name: str) -> bool:
        for i, check in enumerate(self._checks):
            if check.service_name == service_name:
                self._checks.pop(i)
                return True
        return False

    def get_all(self) -> list[HealthCheck]:
        return self._checks.copy()

    def get_by_name(self, service_name: str) -> HealthCheck | None:
        for check in self._checks:
            if check.service_name == service_name:
                return check
        return None
