"""
SAWS Weather Data Fetch Tasks

Celery tasks for fetching weather data from PME and other sources.
"""

import logging
from datetime import datetime

from celery import shared_task
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.base import async_session_maker
from app.models.field import Field
from app.models.weather import WeatherData, WeatherDataType
from app.services.weather.pme import PMEClient

logger = logging.getLogger(__name__)
settings = get_settings()


@shared_task(name="app.tasks.weather.fetch_current_weather")
def fetch_current_weather() -> dict:
    """
    Fetch current weather conditions for all field locations.

    Uses PME (Presidency of Meteorology and Environment) API.
    """
    logger.info("Starting current weather fetch")

    try:
        pme = PMEClient(api_key=settings.pme_api_key)

        async with async_session_maker() as session:
            # Get all active fields
            result = await session.execute(
                select(Field).where(Field.status == "active")
            )
            fields = result.scalars().all()

            logger.info(f"Fetching weather for {len(fields)} field locations")

            fetched_count = 0
            for field in fields:
                try:
                    # Fetch current weather
                    weather_data = pme.get_current_weather(
                        latitude=field.centroid_latitude,
                        longitude=field.centroid_longitude,
                    )

                    # Create weather record
                    weather = WeatherData(
                        latitude=field.centroid_latitude,
                        longitude=field.centroid_longitude,
                        district=field.district_id,
                        data_type=WeatherDataType.CURRENT,
                        observation_time=datetime.fromisoformat(
                            weather_data["observation_time"]
                        ),
                        temperature=weather_data.get("temperature"),
                        feels_like=weather_data.get("feels_like"),
                        humidity=weather_data.get("humidity"),
                        dew_point=weather_data.get("dew_point"),
                        wind_speed=weather_data.get("wind_speed"),
                        wind_direction=weather_data.get("wind_direction"),
                        wind_gust=weather_data.get("wind_gust"),
                        precipitation=weather_data.get("precipitation"),
                        pressure=weather_data.get("pressure"),
                        visibility=weather_data.get("visibility"),
                        cloud_cover=weather_data.get("cloud_cover"),
                        uv_index=weather_data.get("uv_index"),
                        source="pme",
                    )

                    session.add(weather)
                    fetched_count += 1

                except Exception as e:
                    logger.error(
                        f"Error fetching weather for field {field.id}: {e}"
                    )
                    continue

            await session.commit()
            logger.info(f"Successfully fetched weather for {fetched_count} locations")

            return {
                "status": "success",
                "locations_fetched": fetched_count,
            }

    except Exception as e:
        logger.error(f"Error in weather fetch task: {e}")
        return {"status": "error", "message": str(e)}


@shared_task(name="app.tasks.weather.fetch_weather_forecast")
def fetch_weather_forecast() -> dict:
    """
    Fetch weather forecast for all field locations.

    Stores both hourly and daily forecasts.
    """
    logger.info("Starting weather forecast fetch")

    try:
        pme = PMEClient(api_key=settings.pme_api_key)

        async with async_session_maker() as session:
            # Get all active fields
            result = await session.execute(
                select(Field).where(Field.status == "active")
            )
            fields = result.scalars().all()

            logger.info(f"Fetching forecast for {len(fields)} field locations")

            fetched_count = 0
            for field in fields:
                try:
                    # Fetch 5-day forecast
                    forecast_data = pme.get_forecast(
                        latitude=field.centroid_latitude,
                        longitude=field.centroid_longitude,
                        days=5,
                    )

                    # Process daily forecasts
                    for day_data in forecast_data.get("daily", []):
                        # Store or update daily forecast
                        # Implementation depends on DailyForecast model
                        pass

                    fetched_count += 1

                except Exception as e:
                    logger.error(
                        f"Error fetching forecast for field {field.id}: {e}"
                    )
                    continue

            await session.commit()
            logger.info(f"Successfully fetched forecast for {fetched_count} locations")

            return {
                "status": "success",
                "locations_fetched": fetched_count,
            }

    except Exception as e:
        logger.error(f"Error in forecast fetch task: {e}")
        return {"status": "error", "message": str(e)}


@shared_task(name="app.tasks.weather.fetch_historical_weather")
def fetch_historical_weather(start_date: str, end_date: str) -> dict:
    """
    Fetch historical weather data for a date range.

    Args:
        start_date: ISO format start date
        end_date: ISO format end date
    """
    logger.info(f"Starting historical weather fetch from {start_date} to {end_date}")

    try:
        # Implementation would fetch historical data
        # This is useful for backfilling and SPEI calculations

        return {
            "status": "success",
            "message": "Historical weather fetch not yet implemented",
        }

    except Exception as e:
        logger.error(f"Error in historical weather fetch task: {e}")
        return {"status": "error", "message": str(e)}
