"""
SAWS Alert Schemas

Pydantic schemas for alert API validation and serialization.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AlertSeverity(str, Enum):
    """Alert severity levels."""

    CRITICAL = "critical"
    WARNING = "warning"
    ADVISORY = "advisory"
    INFO = "info"


class AlertType(str, Enum):
    """Types of alerts."""

    DROUGHT = "drought"
    LOW_NDVI = "low_ndvi"
    SOIL_MOISTURE = "soil_moisture"
    EXTREME_TEMPERATURE = "extreme_temperature"
    PEST_DETECTION = "pest_detection"
    IRRIGATION_NEEDED = "irrigation_needed"
    FROST_WARNING = "frost_warning"
    HARVEST_READY = "harvest_ready"


class AlertBase(BaseModel):
    """Base alert schema."""

    field_id: str | None = None
    severity: AlertSeverity
    alert_type: AlertType
    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1)
    district: str | None = None
    priority: int = Field(default=0, ge=0, le=100)


class AlertCreate(AlertBase):
    """Schema for creating a new alert."""

    user_id: str
    data: dict[str, Any] | None = None


class AlertUpdate(BaseModel):
    """Schema for updating an alert."""

    title: str | None = None
    message: str | None = None
    priority: int | None = None
    is_read: bool | None = None


class Alert(AlertBase):
    """Alert model for API responses."""

    id: str
    user_id: str
    data: dict[str, Any] | None = None
    is_read: bool = False
    read_at: datetime | None = None
    email_sent: bool = False
    sms_sent: bool = False
    whatsapp_sent: bool = False
    created_at: datetime
    expires_at: datetime | None = None

    class Config:
        from_attributes = True


class AlertListResponse(BaseModel):
    """Paginated list of alerts."""

    total: int
    skip: int
    limit: int
    items: list[Alert]


class AlertSummary(BaseModel):
    """Brief alert information for notifications."""

    id: str
    severity: AlertSeverity
    alert_type: AlertType
    title: str
    is_read: bool
    created_at: datetime


class AlertStats(BaseModel):
    """Alert statistics."""

    total: int
    unread: int
    by_severity: dict[str, int]
    by_type: dict[str, int]
    critical_count: int = 0
