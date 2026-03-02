"""
SAWS Celery Tasks

Background task processing with Celery.
"""

from celery import Celery

from app.config import get_settings

settings = get_settings()

# Create Celery instance
celery_app = Celery(
    "saws",
    broker=settings.celery_broker_url or settings.redis_url,
    backend=settings.celery_result_backend or settings.redis_url,
    include=[
        "app.tasks.satellite_fetch",
        "app.tasks.weather_fetch",
        "app.tasks.index_calculation",
        "app.tasks.drought_monitor",
        "app.tasks.alert_generation",
    ],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Riyadh",
    enable_utc=True,
    task_time_limit=settings.celery_task_time_limit,
    task_soft_time_limit=settings.celery_task_soft_time_limit,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)

# Configure periodic tasks
celery_app.conf.beat_schedule = {
    # Satellite data fetching
    "fetch-modis-daily": {
        "task": "app.tasks.satellite.fetch_modis_data",
        "schedule": 24 * 60 * 60,  # Daily
    },
    "fetch-landsat-daily": {
        "task": "app.tasks.satellite.fetch_landsat_data",
        "schedule": 24 * 60 * 60,  # Daily
    },

    # Weather data fetching
    "fetch-weather-6h": {
        "task": "app.tasks.weather.fetch_current_weather",
        "schedule": 6 * 60 * 60,  # Every 6 hours
    },
    "fetch-weather-forecast-daily": {
        "task": "app.tasks.weather.fetch_weather_forecast",
        "schedule": 24 * 60 * 60,  # Daily
    },

    # Index calculation
    "calculate-ndvi-daily": {
        "task": "app.tasks.indexes.calculate_vegetation_indices",
        "schedule": 24 * 60 * 60,  # Daily
    },

    # Drought monitoring
    "calculate-spei-12h": {
        "task": "app.tasks.drought.calculate_spei",
        "schedule": 12 * 60 * 60,  # Every 12 hours
    },
    "classify-drought-12h": {
        "task": "app.tasks.drought.classify_drought_status",
        "schedule": 12 * 60 * 60,  # Every 12 hours
    },

    # Alert generation
    "generate-alerts-hourly": {
        "task": "app.tasks.alerts.generate_alerts",
        "schedule": 60 * 60,  # Every hour
    },
    "send-notifications-15m": {
        "task": "app.tasks.alerts.send_pending_notifications",
        "schedule": 15 * 60,  # Every 15 minutes
    },
}

__all__ = ["celery_app"]
