"""Health check response models."""
from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel, Field


class ServiceDependencyStatus(BaseModel):
    status: str = Field(..., description="'healthy', 'degraded', or 'unhealthy'")
    latency_ms: Optional[float] = None
    details: Optional[str] = None


class LiveHealthResponse(BaseModel):
    status: str = "live"
    service: str = "GraphWeave"
    version: str = "1.0.0"
    timestamp: datetime


class ReadyHealthResponse(BaseModel):
    status: str = Field(..., description="'ready' or 'not_ready'")
    service: str = "GraphWeave"
    version: str = "1.0.0"
    timestamp: datetime
    dependencies: Dict[str, ServiceDependencyStatus]
