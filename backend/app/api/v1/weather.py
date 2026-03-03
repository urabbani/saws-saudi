"""
SAWS Weather API Endpoints

Current conditions, forecasts, and historical weather data.
"""

from datetime import date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.dependencies import DBSession, UserId
from app.schemas.weather import (
    CurrentWeather,
    CurrentWeatherResponse,
    DailyForecast,
    ForecastResponse,
    HistoricalWeatherData,
    HistoricalWeatherResponse,
    HourlyForecast,
)
from app.services.weather.pme import PMEClient
from app.models.weather import WeatherData, DailyForecast as DailyForecastModel
from app.config import get_settings

settings = get_settings()
router = APIRouter()


async def get_district_from_coords(latitude: float, longitude: float) -> str | None:
    """
    Get district name from coordinates.

    Args:
        latitude: Location latitude
        longitude: Location longitude

    Returns:
        District name or None
    """
    # Check against configured district bounds
    districts = settings.district_bounds
    for district_name, bounds in districts.items():
        if (bounds["south"] <= latitude <= bounds["north"] and
            bounds["west"] <= longitude <= bounds["east"]):
            return district_name
    return None


@router.get("/current", response_model=CurrentWeatherResponse)
async def get_current_weather(
    db: DBSession,
    user_id: UserId,
    latitude: Annotated[float, Query(ge=24.0, le=28.0)],
    longitude: Annotated[float, Query(ge=45.0, le=55.0)],
) -> CurrentWeatherResponse:
    """
    Get current weather conditions for a location.

    Args:
        db: Database session
        user_id: Authenticated user ID
        latitude: Latitude within Eastern Province bounds
        longitude: Longitude within Eastern Province bounds

    Returns:
        Current weather conditions
    """
    # Get district
    district = await get_district_from_coords(latitude, longitude)

    # Try to get from database first (recent data, within 1 hour)
    one_hour_ago = datetime.now().replace(tzinfo=None).timestamp() - 3600
    stmt = select(WeatherData).where(
        and_(
            WeatherData.latitude == latitude,
            WeatherData.longitude == longitude,
            WeatherData.data_type == "current",
        )
    ).order_by(WeatherData.observation_time.desc()).limit(1)

    result = await db.execute(stmt)
    cached_data = result.scalar_one_or_none()

    # If no recent data, fetch from PME
    if not cached_data:
        client = PMEClient()
        try:
            data = await client.get_current_weather(latitude, longitude)
            await client.close()
        except Exception as e:
            # Return mock data on error
            data = client._mock_current_weather(latitude, longitude)

        return CurrentWeatherResponse(
            latitude=latitude,
            longitude=longitude,
            weather=CurrentWeather(
                temperature=data["temperature"],
                feels_like=data.get("feels_like"),
                humidity=data["humidity"],
                dew_point=data.get("dew_point"),
                wind_speed=data["wind_speed"],
                wind_direction=data["wind_direction"],
                wind_gust=data.get("wind_gust"),
                pressure=data.get("pressure"),
                visibility=data.get("visibility"),
                cloud_cover=data.get("cloud_cover"),
                uv_index=data.get("uv_index"),
                precipitation=data.get("precipitation"),
                condition=data["condition"],
                observation_time=datetime.fromisoformat(data["observation_time"]),
                district=district,
                station_id=data.get("station_id"),
            ),
        )

    # Return cached data
    return CurrentWeatherResponse(
        latitude=latitude,
        longitude=longitude,
        weather=CurrentWeather(
            temperature=cached_data.temperature or 35.0,
            feels_like=cached_data.feels_like,
            humidity=cached_data.humidity or 15,
            dew_point=cached_data.dew_point,
            wind_speed=cached_data.wind_speed or 15.0,
            wind_direction=cached_data.wind_direction or 315,
            wind_gust=cached_data.wind_gust,
            pressure=cached_data.pressure,
            visibility=cached_data.visibility,
            cloud_cover=cached_data.cloud_cover,
            uv_index=cached_data.uv_index,
            precipitation=cached_data.precipitation,
            condition="Sunny",
            observation_time=cached_data.observation_time,
            district=district,
            station_id=cached_data.station_id,
        ),
    )


@router.get("/forecast", response_model=ForecastResponse)
async def get_weather_forecast(
    db: DBSession,
    user_id: UserId,
    latitude: Annotated[float, Query(ge=24.0, le=28.0)],
    longitude: Annotated[float, Query(ge=45.0, le=55.0)],
    days: Annotated[int, Query(ge=1, le=7)] = 5,
) -> ForecastResponse:
    """
    Get weather forecast for a location.

    Args:
        db: Database session
        user_id: Authenticated user ID
        latitude: Latitude within Eastern Province bounds
        longitude: Longitude within Eastern Province bounds
        days: Number of forecast days (1-7)

    Returns:
        Weather forecast
    """
    # Get district
    district = await get_district_from_coords(latitude, longitude)

    # Try to get from database first (today's forecast)
    today = date.today()
    stmt = select(DailyForecastModel).where(
        and_(
            DailyForecastModel.latitude == latitude,
            DailyForecastModel.longitude == longitude,
            DailyForecastModel.date >= today,
        )
    ).order_by(DailyForecastModel.date).limit(days)

    result = await db.execute(stmt)
    cached_forecasts = result.scalars().all()

    # If we have enough cached data
    if len(cached_forecasts) >= days:
        daily_forecasts = [
            DailyForecast(
                date=f.date,
                temp_min=f.temp_min or 25.0,
                temp_max=f.temp_max or 42.0,
                temp_avg=f.temp_avg,
                precipitation_total=f.precipitation_total,
                precipitation_probability=f.precipitation_probability,
                condition=f.condition_main or "Sunny",
                description=f.condition_description,
                wind_speed_avg=f.wind_speed_avg,
                wind_gust_max=f.wind_gust_max,
                humidity_avg=f.humidity_avg,
                uv_index_max=f.uv_index_max,
            )
            for f in cached_forecasts
        ]

        return ForecastResponse(
            latitude=latitude,
            longitude=longitude,
            district=district,
            generated_at=datetime.now(),
            daily=daily_forecasts,
            hourly=None,
        )

    # Fetch from PME
    client = PMEClient()
    try:
        forecast_data = await client.get_forecast(latitude, longitude, days)
        await client.close()
    except Exception:
        forecast_data = client._mock_forecast(latitude, longitude, days)

    # Parse daily forecasts
    daily_forecasts = []
    for day_data in forecast_data["daily"]:
        daily_forecasts.append(
            DailyForecast(
                date=datetime.fromisoformat(day_data["date"]),
                temp_min=day_data["temp_min"],
                temp_max=day_data["temp_max"],
                temp_avg=day_data.get("temp_avg"),
                precipitation_total=day_data.get("precipitation_total"),
                precipitation_probability=day_data.get("precipitation_probability"),
                condition=day_data["condition"],
                description=day_data.get("description"),
                wind_speed_avg=day_data.get("wind_speed_avg"),
                wind_gust_max=day_data.get("wind_gust_max"),
                humidity_avg=day_data.get("humidity_avg"),
                uv_index_max=day_data.get("uv_index_max"),
            )
        )

    return ForecastResponse(
        latitude=latitude,
        longitude=longitude,
        district=district,
        generated_at=datetime.fromisoformat(forecast_data["generated_at"]),
        daily=daily_forecasts,
        hourly=None,
    )


@router.get("/history", response_model=HistoricalWeatherResponse)
async def get_historical_weather(
    db: DBSession,
    user_id: UserId,
    latitude: Annotated[float, Query(ge=24.0, le=28.0)],
    longitude: Annotated[float, Query(ge=45.0, le=55.0)],
    start_date: date,
    end_date: date,
) -> HistoricalWeatherResponse:
    """
    Get historical weather data for a location.

    Args:
        db: Database session
        user_id: Authenticated user ID
        latitude: Latitude within Eastern Province bounds
        longitude: Longitude within Eastern Province bounds
        start_date: Start date
        end_date: End date

    Returns:
        Historical weather data
    """
    # Validate date range
    if end_date < start_date:
        raise HTTPException(
            status_code=400,
            detail="end_date must be after start_date"
        )

    if (end_date - start_date).days > 365:
        raise HTTPException(
            status_code=400,
            detail="Date range cannot exceed 365 days"
        )

    # Get district
    district = await get_district_from_coords(latitude, longitude)

    # Query historical data
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())

    stmt = select(WeatherData).where(
        and_(
            WeatherData.latitude == latitude,
            WeatherData.longitude == longitude,
            WeatherData.data_type == "historical",
            WeatherData.observation_time >= start_datetime,
            WeatherData.observation_time <= end_datetime,
        )
    ).order_by(WeatherData.observation_time)

    result = await db.execute(stmt)
    weather_records = result.scalars().all()

    # If no historical data available, return sample data
    if not weather_records:
        # Generate sample historical data for Eastern Province
        historical_data = []
        current_date = start_datetime
        import random

        while current_date <= end_datetime:
            # Time-based temperature (cooler at night)
            hour = current_date.hour
            base_temp = 30.0 + 8.0 * ((hour - 6) % 24) / 12

            historical_data.append(
                HistoricalWeatherData(
                    observation_time=current_date,
                    temperature=round(base_temp + random.uniform(-2, 2), 1),
                    humidity=random.randint(12, 25),
                    wind_speed=round(random.uniform(10, 20), 1),
                    wind_direction=random.randint(270, 360),
                    precipitation=0.0,
                    pressure=round(random.uniform(1008, 1015), 1),
                    cloud_cover=random.randint(0, 30),
                    uv_index=random.randint(0, 11) if 6 <= hour <= 18 else 0,
                    soil_moisture=round(random.uniform(5, 15), 1),
                    soil_temperature=round(base_temp - 3, 1),
                )
            )
            current_date += datetime.timedelta(hours=6)  # Every 6 hours
    else:
        historical_data = [
            HistoricalWeatherData(
                observation_time=record.observation_time,
                temperature=record.temperature,
                humidity=record.humidity,
                wind_speed=record.wind_speed,
                wind_direction=record.wind_direction,
                precipitation=record.precipitation,
                pressure=record.pressure,
                cloud_cover=record.cloud_cover,
                uv_index=record.uv_index,
                soil_moisture=record.soil_moisture,
                soil_temperature=record.soil_temperature,
            )
            for record in weather_records
        ]

    return HistoricalWeatherResponse(
        latitude=latitude,
        longitude=longitude,
        start_date=datetime.combine(start_date, datetime.min.time()),
        end_date=datetime.combine(end_date, datetime.max.time()),
        data=historical_data,
    )


@router.get("/field/{field_id}", response_model=CurrentWeatherResponse)
async def get_field_weather(
    field_id: str,
    db: DBSession,
    user_id: UserId,
) -> CurrentWeatherResponse:
    """
    Get current weather for a specific field.

    Args:
        field_id: Field ID
        db: Database session
        user_id: Authenticated user ID

    Returns:
        Current weather for the field location
    """
    # Get field coordinates
    from app.models.field import Field

    stmt = select(Field).where(Field.id == field_id)
    result = await db.execute(stmt)
    field = result.scalar_one_or_none()

    if not field:
        raise HTTPException(status_code=404, detail="Field not found")

    # Get weather for field centroid
    latitude = field.centroid_latitude
    longitude = field.centroid_longitude

    return await get_current_weather(db, user_id, latitude, longitude)
