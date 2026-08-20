from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AnalyticsLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    endpoint: str
    method: str
    timestamp: datetime
    response_time_ms: float
