# SAWS Backend

Saudi AgriDrought Warning System - Production Backend API

## Overview

This is the FastAPI backend for SAWS, providing:
- RESTful API for satellite and weather data
- Google Earth Engine integration
- Drought monitoring (SPEI-based)
- Real-time alert system
- Celery background tasks
- PostgreSQL + PostGIS + TimescaleDB

## Technology Stack

- **Python 3.12**
- **FastAPI 0.115.0** - Web framework
- **PostgreSQL** + **PostGIS** - Geospatial database
- **TimescaleDB** - Time-series data
- **Redis** - Caching and Celery broker
- **Celery** - Background tasks
- **Google Earth Engine** - Satellite data processing
- **SQLAlchemy 2.0** - ORM

## Project Structure

```
backend/
├── app/
│   ├── api/v1/          # API endpoints
│   ├── core/            # Security and auth
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic
│   │   ├── satellite/   # GEE integration
│   │   ├── weather/     # PME API
│   │   ├── drought/     # SPEI calculation
│   │   └── alert/       # Alert generation
│   ├── tasks/           # Celery tasks
│   ├── db/              # Database setup
│   ├── utils/           # Utilities
│   ├── main.py          # Application entry
│   ├── config.py        # Configuration
│   ├── dependencies.py  # Dependency injection
│   └── middleware.py    # Custom middleware
├── ml/                  # Machine Learning models
├── etl/                 # Data pipelines
├── scripts/             # Utility scripts
├── tests/               # Test suite
└── requirements/        # Dependencies
```

## Setup

### Prerequisites

- Python 3.12+
- PostgreSQL 16+ with PostGIS and TimescaleDB
- Redis 7+
- Google Cloud service account (for Earth Engine)

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements/dev.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Initialize database
python scripts/init_db.py

# Seed with Eastern Province data
python scripts/seed_data.py
```

### Environment Variables

```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_USER=saws_user
DB_PASSWORD=saws_password
DB_NAME=saws_db

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Google Earth Engine
GEE_SERVICE_ACCOUNT_KEY_PATH=/path/to/key.json
GEE_PROJECT_ID=your-project-id

# Weather API (PME)
PME_API_KEY=your-pme-api-key

# Security
SECRET_KEY=your-secret-key-min-32-characters
ALGORITHM=HS256
```

## Running the Application

### Development Server

```bash
# Run FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run Celery worker
celery -A app.tasks worker --loglevel=info

# Run Celery beat (scheduler)
celery -A app.tasks beat --loglevel=info
```

### Production

```bash
# Using gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker

# Using Docker Compose
docker-compose up -d
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## Main API Endpoints

### Fields
- `GET /api/v1/fields` - List all fields
- `GET /api/v1/fields/{id}` - Get field details
- `POST /api/v1/fields` - Create field
- `PUT /api/v1/fields/{id}` - Update field
- `DELETE /api/v1/fields/{id}` - Delete field

### Satellite Data
- `GET /api/v1/satellite/sources` - Available satellites
- `GET /api/v1/satellite/images` - Satellite imagery
- `GET /api/v1/satellite/indices/{field_id}` - Vegetation indices

### Weather
- `GET /api/v1/weather/current` - Current conditions
- `GET /api/v1/weather/forecast` - Weather forecast
- `GET /api/v1/weather/history` - Historical data

### Drought
- `GET /api/v1/drought/status` - Current drought status
- `GET /api/v1/drought/forecast` - Drought prediction
- `GET /api/v1/analytics/trends` - Crop trends

### Alerts
- `GET /api/v1/alerts` - List alerts
- `POST /api/v1/alerts` - Create alert
- `PUT /api/v1/alerts/{id}/read` - Mark as read
- `WS /api/v1/ws/alerts` - Real-time alerts (WebSocket)

## Vegetation Indices

The system calculates 20+ vegetation indices:

### Core Indices
- **NDVI**: Normalized Difference Vegetation Index
- **EVI**: Enhanced Vegetation Index
- **SAVI**: Soil Adjusted Vegetation Index
- **MSAVI**: Modified SAVI (for arid regions)

### Drought Monitoring
- **NDMI**: Normalized Difference Moisture Index
- **NDWI**: Normalized Difference Water Index
- **VHI**: Vegetation Health Index (WMO standard)
- **TCI**: Temperature Condition Index
- **VCI**: Vegetation Condition Index

### Saudi Arabia Specific
- **Oasis Health Index**: For date palm oases
- **Aridity Index**: UNEP classification
- **Desertification Index**: Sand exposure risk
- **Thermal Stress Index**: Crop-specific heat stress

## Drought Monitoring

The system uses **SPEI** (Standardized Precipitation Evapotranspiration Index)
following WMO recommendations:

- **SPEI-3**: Agricultural drought (3 months)
- **SPEI-6**: Hydrological drought onset (6 months)
- **SPEI-12**: Long-term drought patterns (12 months)

### Classification

| SPEI Value | Classification | Action Required |
|------------|----------------|-----------------|
| ≤ -2.5 | Extreme Drought | Emergency measures |
| -2.5 to -2.0 | Severe Drought | Water rationing |
| -2.0 to -1.5 | Moderate Drought | Reduce usage |
| -1.5 to -1.0 | Mild Drought | Monitor |
| > -1.0 | Normal | No action |

## Saudi Government Compliance

### Data Localization
- All data stored in Saudi data centers (SDAIA National Cloud)
- No cross-border data transfer without approval

### Security Standards
- AES-256 encryption at rest
- TLS 1.3 for data in transit
- Multi-factor authentication
- 5-year log retention (NCA requirement)

### Certifications
- **ISO 27001**: Information security (6 months)
- **NCA ECC**: Essential Cybersecurity Controls (3 months)
- **PDPL**: Personal Data Protection Law compliance

## Background Tasks

CeleryBeat schedules:

| Task | Schedule | Description |
|------|----------|-------------|
| fetch_modis_data | Daily | Fetch MODIS imagery |
| fetch_landsat_data | Daily | Fetch Landsat imagery |
| fetch_current_weather | 6 hours | Current conditions |
| calculate_spei | 12 hours | Drought index |
| generate_alerts | Hourly | Alert processing |
| send_notifications | 15 min | Pending alerts |

## Development

### Running Tests

```bash
# Unit tests
pytest tests/

# Coverage report
pytest --cov=app --cov-report=html

# Integration tests
pytest tests/integration/
```

### Code Quality

```bash
# Type checking
mypy app/

# Linting
ruff check app/

# Format code
ruff format app/
```

## Deployment

### Docker

```bash
# Build
docker build -f deployments/docker/Dockerfile.backend -t saws-backend .

# Run
docker run -p 8000:8000 saws-backend
```

### Kubernetes

```bash
kubectl apply -f deployments/kubernetes/backend.yaml
```

## License

Copyright © 2026 Saudi AgriDrought Warning System
Ministry of Environment, Water and Agriculture

## Support

For technical support, contact: tech@saws.gov.sa
