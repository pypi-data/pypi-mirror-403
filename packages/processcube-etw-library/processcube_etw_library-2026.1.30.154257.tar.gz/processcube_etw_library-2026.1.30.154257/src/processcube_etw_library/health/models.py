from datetime import timedelta

from pydantic import BaseModel, Field, field_serializer


class HealthCheckEntityModel(BaseModel):
    service: str
    status: str = "healthy"
    time_taken: timedelta = Field(default=timedelta())
    tags: list[str] = Field(default_factory=list)
    comments: list[str] = Field(default_factory=list)

    @field_serializer("time_taken")
    def serialize_time_taken(self, time: timedelta) -> str:
        return str(time)


class HealthCheckModel(BaseModel):
    status: str = "healthy"
    total_time_taken: timedelta = Field(default=timedelta())
    entities: list[HealthCheckEntityModel] = Field(default_factory=list)

    @field_serializer("total_time_taken")
    def serialize_total_time_taken(self, time: timedelta) -> str:
        return str(time)


class LivezResponse(BaseModel):
    status: str = Field(default="alive", description="Liveness status")


class HealthConditionInfo(BaseModel):
    service_name: str = Field(..., description="Name of the service")
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
    comments: list[str] = Field(default_factory=list, description="Comments describing the check")

class HealthCheckResult(BaseModel):
    healthy: bool = Field(..., description="Indicates if the health check passed")
    time_taken: timedelta = Field(..., description="Time taken to perform the health check")

    @field_serializer("time_taken")
    def serialize_time_taken(self, time: timedelta) -> str:
        return str(time)
