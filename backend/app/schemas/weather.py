"""
SAWS Weather Schemas

Pydantic schemas for weather API validation and serialization.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CurrentWeather(BaseModel):
    """Current weather conditions."""

    temperature: float  # Celsius
    feels_like: float | None = None
    humidity: int  # Percentage
    dew_point: float | None = None
    wind_speed: float  # km/h
    wind_direction: int  # Degrees
    wind_gust: float | None = None
    pressure: float | None = None  # hPa
    visibility: float | None = None  # km
    cloud_cover: int | None = None  # Percentage
    uv_index: int | None = None
    precipitation: float | None = None  # mm
    condition: str  # e.g., "Clear", "Partly Cloudy"
    observation_time: datetime
    district: str | None = None
    station_id: str | None = None


class CurrentWeatherResponse(BaseModel):
    """Current weather response."""

    latitude: float
    longitude: float
    weather: CurrentWeather


class HourlyForecast(BaseModel):
    """Hourly weather forecast."""

    datetime: datetime
    temperature: float
    feels_like: float | None = None
    humidity: int
    wind_speed: float
    wind_direction: int
    precipitation: float | None = None
    precipitation_probability: int | None = None
    cloud_cover: int | None = None
    uv_index: int | None = None
    condition: str


class DailyForecast(BaseModel):
    """Daily weather forecast."""

    date: datetime
    temp_min: float
    temp_max: float
    temp_avg: float | None = None
    precipitation_total: float | None = None
    precipitation_probability: int | None = None
    condition: str
    description: str | None = None
    wind_speed_avg: float | None = None
    wind_gust_max: float | None = None
    humidity_avg: int | None = None
    uv_index_max: int | None = None


class ForecastResponse(BaseModel):
    """Weather forecast response."""

    latitude: float
    longitude: float
    district: str | None = None
    generated_at: datetime
    daily: list[DailyForecast]
    hourly: list[HourlyForecast] | None = None


class HistoricalWeatherData(BaseModel):
    """Historical weather observation."""

    observation_time: datetime
    temperature: float | None = None
    humidity: int | None = None
    wind_speed: float | None = None
    wind_direction: int | None = None
    precipitation: float | None = None
    pressure: float | None = None
    cloud_cover: int | None = None
    uv_index: int | None = None
    soil_moisture: float | None = None
    soil_temperature: float | None = None


class HistoricalWeatherResponse(BaseModel):
    """Historical weather response."""

    latitude: float
    longitude: float
    start_date: datetime
    end_date: datetime
    data: list[HistoricalWeatherData]
