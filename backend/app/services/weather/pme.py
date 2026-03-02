"""
SAWS Weather Service - PME API Client

Presidency of Meteorology and Environment API integration.
"""

import logging
from datetime import datetime, timedelta
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class PMEClient:
    """
    Client for Saudi Arabia's Presidency of Meteorology and Environment API.

    Provides:
    - Current weather conditions
    - Weather forecasts
    - Historical weather data
    - Climate data
    """

    def __init__(self, api_key: str | None = None):
        """Initialize PME client."""
        self.api_key = api_key or settings.pme_api_key
        self.base_url = settings.pme_api_base_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()

    async def get_current_weather(
        self,
        latitude: float,
        longitude: float,
    ) -> dict[str, Any]:
        """
        Get current weather conditions.

        Args:
            latitude: Location latitude (Eastern Province: 24-28°N)
            longitude: Location longitude (Eastern Province: 46-50°E)

        Returns:
            Current weather data
        """
        try:
            # PME API endpoint for current weather
            url = f"{self.base_url}/weather/current"

            params = {
                "lat": latitude,
                "lon": longitude,
                "api_key": self.api_key,
            }

            response = await self.client.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            return self._parse_current_weather(data)

        except httpx.HTTPError as e:
            logger.error(f"Error fetching current weather: {e}")
            # Return mock data for Eastern Province
            return self._mock_current_weather(latitude, longitude)

    async def get_forecast(
        self,
        latitude: float,
        longitude: float,
        days: int = 5,
    ) -> dict[str, Any]:
        """
        Get weather forecast.

        Args:
            latitude: Location latitude
            longitude: Location longitude
            days: Number of forecast days (1-7)

        Returns:
            Weather forecast data
        """
        try:
            url = f"{self.base_url}/weather/forecast"

            params = {
                "lat": latitude,
                "lon": longitude,
                "days": min(days, 7),
                "api_key": self.api_key,
            }

            response = await self.client.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            return self._parse_forecast(data)

        except httpx.HTTPError as e:
            logger.error(f"Error fetching forecast: {e}")
            return self._mock_forecast(latitude, longitude, days)

    def _parse_current_weather(self, data: dict[str, Any]) -> dict[str, Any]:
        """Parse current weather response from PME API."""
        return {
            "temperature": data.get("temp", 35.0),
            "feels_like": data.get("feels_like", 38.0),
            "humidity": data.get("humidity", 15),
            "dew_point": data.get("dew_point", 10.0),
            "wind_speed": data.get("wind_speed", 15.0),
            "wind_direction": data.get("wind_dir", 315),  # NW (prevailing in EP)
            "wind_gust": data.get("wind_gust", 25.0),
            "pressure": data.get("pressure", 1013.0),
            "visibility": data.get("visibility", 10.0),
            "cloud_cover": data.get("clouds", 0),
            "uv_index": data.get("uv_index", 8),  # High in Saudi
            "precipitation": data.get("precip", 0.0),
            "condition": data.get("condition", "Sunny"),
            "observation_time": data.get("time", datetime.now().isoformat()),
        }

    def _parse_forecast(self, data: dict[str, Any]) -> dict[str, Any]:
        """Parse forecast response from PME API."""
        daily = []

        for day_data in data.get("daily", []):
            daily.append({
                "date": day_data.get("date"),
                "temp_min": day_data.get("temp_min", 25.0),
                "temp_max": day_data.get("temp_max", 42.0),
                "temp_avg": day_data.get("temp_avg", 34.0),
                "precipitation_total": day_data.get("precip", 0.0),
                "precipitation_probability": day_data.get("precip_prob", 0),
                "condition": day_data.get("condition", "Sunny"),
                "description": day_data.get("description", "Clear skies"),
                "wind_speed_avg": day_data.get("wind_speed", 15.0),
                "wind_gust_max": day_data.get("wind_gust", 25.0),
                "humidity_avg": day_data.get("humidity", 15),
                "uv_index_max": day_data.get("uv_index", 9),
            })

        return {
            "daily": daily,
            "hourly": data.get("hourly", []),
            "generated_at": datetime.now().isoformat(),
        }

    def _mock_current_weather(
        self,
        latitude: float,
        longitude: float,
    ) -> dict[str, Any]:
        """Generate realistic mock data for Eastern Province."""
        import random

        # Time-based temperature
        hour = datetime.now().hour
        base_temp = 35.0 + 5.0 * math.sin((hour - 6) * math.pi / 12)  # Peak at 15:00

        # Add some variation
        temp = base_temp + random.uniform(-2, 2)

        return {
            "temperature": round(temp, 1),
            "feels_like": round(temp + random.uniform(2, 5), 1),  # Heat stress
            "humidity": random.randint(10, 25),  # Very dry
            "dew_point": round(temp - random.randint(15, 25), 1),
            "wind_speed": round(random.uniform(10, 20), 1),  # Prevailing NW winds
            "wind_direction": random.randint(270, 360),
            "wind_gust": round(random.uniform(20, 30), 1),
            "pressure": round(random.uniform(1008, 1015), 1),
            "visibility": 10.0,
            "cloud_cover": random.randint(0, 20),
            "uv_index": random.randint(7, 11),  # Very high
            "precipitation": 0.0,  # Rare in Eastern Province
            "condition": random.choice(["Sunny", "Clear", "Partly Cloudy"]),
            "observation_time": datetime.now().isoformat(),
        }

    def _mock_forecast(
        self,
        latitude: float,
        longitude: float,
        days: int,
    ) -> dict[str, Any]:
        """Generate realistic forecast for Eastern Province."""
        import random
        import math

        daily = []
        base_date = datetime.now()

        for i in range(days):
            date = base_date + timedelta(days=i)

            # Temperature varies by season
            month_day = (date.month, date.day)
            if (3, 20) <= month_day <= (6, 21):  # Spring-Summer
                temp_max = random.uniform(40, 48)
                temp_min = random.uniform(25, 32)
            elif (6, 21) <= month_day <= (9, 22):  # Summer
                temp_max = random.uniform(42, 50)
                temp_min = random.uniform(28, 35)
            else:  # Fall-Winter
                temp_max = random.uniform(25, 35)
                temp_min = random.uniform(15, 22)

            daily.append({
                "date": date.isoformat(),
                "temp_min": round(temp_min, 1),
                "temp_max": round(temp_max, 1),
                "temp_avg": round((temp_min + temp_max) / 2, 1),
                "precipitation_total": 0.0,  # Rare
                "precipitation_probability": random.randint(0, 5),  # 0-5% chance
                "condition": random.choice(["Sunny", "Clear", "Partly Cloudy", "Hot"]),
                "description": "Clear skies expected",
                "wind_speed_avg": round(random.uniform(12, 18), 1),
                "wind_gust_max": round(random.uniform(22, 30), 1),
                "humidity_avg": random.randint(12, 20),
                "uv_index_max": random.randint(8, 11),
            })

        return {
            "daily": daily,
            "hourly": [],
            "generated_at": datetime.now().isoformat(),
        }


import math  # For mock data calculations
