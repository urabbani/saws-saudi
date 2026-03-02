"""
SAWS Weather Data Model

Current conditions, forecasts, and historical weather data.
"""

from datetime import datetime
from enum import Enum as PyEnum
from uuid import uuid4

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WeatherDataType(str, PyEnum):
    """Types of weather data."""

    CURRENT = "current"  # Current conditions
    FORECAST = "forecast"  # Future prediction
    HISTORICAL = "historical"  # Past observations


class WeatherData(Base):
    """
    Weather observations and forecasts.

    Stores data from PME (Presidency of Meteorology and Environment)
    and other weather sources for the Eastern Province.
    """

    __tablename__ = "weather_data"

    # Primary key
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: uuid4().hex,
    )

    # Location (point data)
    latitude: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    station_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    # Data type
    data_type: Mapped[str] = mapped_column(
        Enum("current", "forecast", "historical", name="weather_data_type"),
        nullable=False,
        index=True,
    )

    # Timestamp
    observation_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    # Temperature (Celsius)
    temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
    dew_point: Mapped[float | None] = mapped_column(Float, nullable=True)
    feels_like: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Humidity
    humidity: Mapped[int | None] = mapped_column(Integer, nullable=True)  # Percentage

    # Wind
    wind_speed: Mapped[float | None] = mapped_column(Float, nullable=True)  # km/h
    wind_direction: Mapped[int | None] = mapped_column(Integer, nullable=True)  # Degrees
    wind_gust: Mapped[float | None] = mapped_column(Float, nullable=True)  # km/h

    # Precipitation
    precipitation: Mapped[float | None] = mapped_column(Float, nullable=True)  # mm
    snow: Mapped[float | None] = mapped_column(Float, nullable=True)  # mm (rare in EP)

    # Pressure
    pressure: Mapped[float | None] = mapped_column(Float, nullable=True)  # hPa

    # Visibility
    visibility: Mapped[float | None] = mapped_column(Float, nullable=True)  # km

    # Cloud cover
    cloud_cover: Mapped[int | None] = mapped_column(Integer, nullable=True)  # Percentage

    # UV Index
    uv_index: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Soil data (if available from sensors)
    soil_moisture: Mapped[float | None] = mapped_column(Float, nullable=True)  # Percentage
    soil_temperature: Mapped[float | None] = mapped_column(Float, nullable=True)  # Celsius

    # Source
    source: Mapped[str] = mapped_column(String(100), nullable=False, default="pme")

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<WeatherData(id={self.id}, type={self.data_type}, time={self.observation_time})>"


class DailyForecast(Base):
    """
    Daily weather forecast summary.

    Aggregates hourly forecasts into daily summaries.
    """

    __tablename__ = "daily_forecasts"

    # Primary key
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: uuid4().hex,
    )

    # Location
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Date
    date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    # Temperature range
    temp_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    temp_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    temp_avg: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Precipitation
    precipitation_total: Mapped[float | None] = mapped_column(Float, nullable=True)
    precipitation_probability: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Conditions
    condition_main: Mapped[str | None] = mapped_column(String(50), nullable=True)  # e.g., "Clear"
    condition_description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Wind
    wind_speed_avg: Mapped[float | None] = mapped_column(Float, nullable=True)
    wind_gust_max: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Humidity
    humidity_avg: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # UV Index
    uv_index_max: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<DailyForecast(date={self.date}, temp_min={self.temp_min}, temp_max={self.temp_max})>"
