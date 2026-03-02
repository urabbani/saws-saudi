"""
SAWS Alert Model

Drought and crop health alerts.
"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.field import Field


class AlertSeverity(str, Enum):
    """Alert severity levels following WMO standards."""

    CRITICAL = "critical"  # Extreme drought, crop failure imminent
    WARNING = "warning"  # Moderate to severe drought
    ADVISORY = "advisory"  # Abnormal conditions detected
    INFO = "info"  # Informational updates


class AlertType(str, Enum):
    """Types of alerts."""

    DROUGHT = "drought"  # Drought condition detected
    LOW_NDVI = "low_ndvi"  # Vegetation health decline
    SOIL_MOISTURE = "soil_moisture"  # Low soil moisture
    EXTREME_TEMPERATURE = "extreme_temperature"  # Heat stress
    PEST_DETECTION = "pest_detection"  # Pest outbreak risk
    IRRIGATION_NEEDED = "irrigation_needed"  # Irrigation recommendation
    FROST_WARNING = "frost_warning"  # Frost risk (rare in EP)
    HARVEST_READY = "harvest_ready"  # Optimal harvest time


class Alert(Base):
    """
    Alert representation for drought monitoring and crop health.

    Alerts are generated automatically based on:
    - SPEI thresholds
    - NDVI anomalies
    - Weather conditions
    - ML predictions
    """

    __tablename__ = "alerts"

    # Primary key
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: uuid4().hex,
    )

    # User who should receive this alert
    user_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Associated field (optional for regional alerts)
    field_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("fields.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Alert classification
    severity: Mapped[str] = mapped_column(
        Enum(AlertSeverity, name="alert_severity", create_constraint=True),
        nullable=False,
        index=True,
    )
    alert_type: Mapped[str] = mapped_column(
        Enum(AlertType, name="alert_type", create_constraint=True),
        nullable=False,
        index=True,
    )

    # Alert content
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    # Location information
    district: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    # Alert data (JSON)
    # Stores SPEI value, NDVI anomaly, temperature, etc.
    data: Mapped[dict | None] = mapped_column(
        func.jsonb,
        nullable=True,
    )

    # Status
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Notification status
    email_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sms_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    whatsapp_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Priority for sorting (higher = more important)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    field: Mapped["Field"] = relationship("Field", back_populates="alerts")

    def __repr__(self) -> str:
        return f"<Alert(id={self.id}, severity={self.severity}, type={self.alert_type})>"
