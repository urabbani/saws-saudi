# Saudi AgriDrought Warning System (SAWS)

<div align="center">

![SAWS Logo](public/logo.jpg)

**Saudi AgriDrought Warning System**

A comprehensive full-stack agricultural drought monitoring platform for Saudi Arabia's Eastern Province

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12-green.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-red.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19.2-blue.svg)](https://react.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://www.postgresql.org/)
[![PostGIS](https://img.shields.io/badge/PostGIS-3.4-orange.svg)](https://postgis.net/)

</div>

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Scientific Improvements (March 2026)](#scientific-improvements-march-2026)
- [Technology Stack](#technology-stack)
- [Quick Start](#quick-start)
- [Development Setup](#development-setup)
- [API Documentation](#api-documentation)
- [Vegetation Indices](#vegetation-indices)
- [Drought Monitoring](#drought-monitoring)
- [Geographic Coverage](#geographic-coverage)
- [Architecture](#architecture)
- [Saudi Government Compliance](#saudi-government-compliance)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

**SAWS** (Saudi AgriDrought Warning System) is a production-ready, full-stack agricultural monitoring platform designed specifically for Saudi Arabia's Eastern Province. Developed under Saudi Vision 2030 Food Security Program, it combines satellite imagery processing, weather data integration, and machine learning to provide real-time drought monitoring and crop health assessment.

### What Makes SAWS Unique?

- **Saudi-Specific**: Built for Eastern Province's unique arid agriculture (2M+ date palms in Al-Hasa)
- **Production-Ready**: Full async FastAPI backend with PostgreSQL+PostGIS, not a demo
- **20+ Vegetation Indices**: Including custom indices for Saudi arid regions
- **WMO Compliant**: SPEI drought classification following World Meteorological Organization standards
- **Government-Ready**: SDAIA, NCA, and PDPL compliant for Saudi government deployment

---

## Features

### Satellite Data Integration

| Satellite | Resolution | Frequency | Use Case |
|-----------|------------|-----------|----------|
| **MODIS** | 250m | Daily (16-day composite) | Operational monitoring |
| **Sentinel-1** (SAR) | 5m | 6-day | Soil moisture, irrigation |
| **Sentinel-2** | 10m | 5-day | Field-scale analysis |
| **Landsat 8-9** | 30m | 16-day | Historical trends (1972+) |

### Real-Time Monitoring

- 🛰️ **Daily Satellite Updates**: MODIS imagery processed via Google Earth Engine
- 🌡️ **6-Hourly Weather**: PME (Presidency of Meteorology & Environment) data
- ⚠️ **Real-Time Alerts**: WebSocket notifications for critical conditions
- 📊 **Live Dashboards**: React Query with automatic refetching

### Drought & Health Assessment

- **SPEI Calculation**: 3, 6, and 12-month Standardized Precipitation Evapotranspiration Index
- **Crop Health**: NDVI, EVI, SAVI with Saudi-specific thresholds
- **Water Stress**: NDMI (Normalized Difference Moisture Index)
- **Thermal Stress**: LST (Land Surface Temperature) anomaly detection
- **Soil Moisture**: SAR-based backscatter analysis (Sentinel-1)

### Saudi-Specific Features

- **Date Palm Health Index**: Custom algorithm for 2M+ Al-Hasa date palms
- **Oasis Health Index**: Monitors traditional oasis ecosystems
- **Dust Storm Detection**: Shamal wind impact assessment
- **Arid Region NDVI**: Corrected for bright sandy soils (30% sand content)
- **Thermal Stress Index**: Crop-specific thresholds for 45-50°C summers

---

## Scientific Improvements (March 2026)

A comprehensive scientific audit was conducted in March 2026 to ensure WMO compliance and scientific accuracy. Key improvements include:

### Critical Fixes

| Issue | Before | After | Status |
|-------|--------|-------|--------|
| **SPEI Methodology** | Simple z-score | Log-logistic distribution (Vicente-Serrano 2010) | ✅ Fixed |
| **Eastern Province Bounds** | 49°E (excluded Hafar Al-Batin) | 45°E (includes all districts) | ✅ Fixed |
| **NDVI Classification** | Generic thresholds | Crop-specific + phenology-aware | ✅ Enhanced |
| **Validation** | None | Comprehensive bounds checking | ✅ Added |
| **Uncertainty** | Not quantified | Full error propagation | ✅ Implemented |

### New Scientific Capabilities

- **Crop-Specific NDVI Thresholds**: Dates, Wheat, Tomatoes, Alfalfa, Sorghum, Citrus
- **Phenology Stage Detection**: Complete growth stage modeling for Saudi crops
- **Time-Series Anomaly Detection**: Z-score + change point detection (SPC)
- **FAO-56 Penman-Monteith ET**: Full reference evapotranspiration calculation
- **Index Validation**: Quality flags, uncertainty bounds, confidence intervals

### Scientific References

- Vicente-Serrano et al. (2010) - SPEI methodology
- WMO & GWP (2016) - Drought monitoring handbook
- FAO-56 (Allen et al., 1998) - Evapotranspiration
- Al-Bakri et al. (2011) - Saudi date palm research

**Full Details**: See [SCIENTIFIC_IMPROVEMENTS.md](docs/SCIENTIFIC_IMPROVEMENTS.md)

---

## Technology Stack

### Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| React | 19.2 | UI framework |
| TypeScript | 5.8 | Type safety |
| Vite | 7.2 | Build tool & HMR |
| Tailwind CSS | 3.4 | Styling with desert theme |
| Shadcn/ui | Latest | 50+ reusable components |
| Leaflet | 1.9.4 | GIS mapping |
| React Leaflet | 5.0 | React Leaflet integration |
| Chart.js | 4.5 | Data visualization |
| Recharts | 2.15 | Charts |
| React Query | 5.0 | Server state management |
| Sonner | 2.0 | Toast notifications |
| Axios | 1.13 | HTTP client |

### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.12 | Runtime |
| FastAPI | 0.115 | Async web framework |
| Uvicorn | 0.32 | ASGI server |
| SQLAlchemy | 2.0 | Async ORM |
| Alembic | 1.14 | Database migrations |
| PostgreSQL | 16 | Relational database |
| PostGIS | 3.4 | Geospatial extensions |
| TimescaleDB | 2.16 | Time-series optimization |
| Redis | 7.0 | Caching & broker |
| Celery | 5.4 | Background tasks |
| Google Earth Engine | 1.0 | Satellite processing |
| Pydantic | 2.10 | Data validation |

### ML & Data Science

- TensorFlow 2.18 for CNN-LSTM drought prediction
- scikit-learn 1.6 for ensemble methods
- XGBoost 2.1 for gradient boosting
- xarray 2024.10 for raster processing
- GeoPandas 1.0 for spatial analysis

---

## Quick Start

### Prerequisites

```bash
# Check versions
node --version    # v20+
python --version  # 3.12+
psql --version    # 16+
redis-cli --version  # 7+
```

### Using Docker (Recommended)

```bash
# Clone repository
git clone https://github.com/urabbani/saws-saudi.git
cd saws-saudi

# Copy environment files
cp .env.example .env

# Start all services
docker-compose up -d

# Initialize database
docker-compose exec backend python scripts/init_db.py
docker-compose exec backend python scripts/seed_data.py
```

**Access the application:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs (Swagger): http://localhost:8000/docs
- API Docs (ReDoc): http://localhost:8000/redoc

---

## Development Setup

### Frontend Development

```bash
# Install dependencies (WSL workaround)
npm install --no-bin-links

# Start development server
node node_modules/vite/bin/vite.js --host 0.0.0.0 --port 3000
```

**Alternative (if npm install fails)**:
```bash
# Direct node execution
node node_modules/vite/bin/vite.js --host 0.0.0.0 --port 3000
```

**Access Frontend**: http://localhost:3000

### Backend Development

```bash
cd backend

# Install dependencies (WSL/Windows filesystem - use system Python)
pip install --user -r requirements/base.txt
pip install --user -r requirements/geospatial.txt
pip install --user orjson

# Run development server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**WSL Note**: On Windows filesystem (mnt/d/), virtual environments have symlink issues. Install to user directory with `pip install --user`.

**Access Backend**: http://localhost:8000
**API Docs**: http://localhost:8000/docs (when DEBUG=true)

### Database Setup

```bash
# PostgreSQL with PostGIS and TimescaleDB
createdb saws_db
psql -d saws_db -c "CREATE EXTENSION postgis;"
psql -d saws_db -c "CREATE EXTENSION timescaledb;"

# Run migrations
cd backend
alembic upgrade head

# Seed with Eastern Province data
python scripts/seed_data.py
```

### Environment Configuration

Create `.env` file in project root:

```bash
# Frontend
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/api/v1/ws/alerts

# Backend Database
DB_HOST=localhost
DB_PORT=5432
DB_USER=saws_user
DB_PASSWORD=saws_password
DB_NAME=saws_db

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# Security
SECRET_KEY=your-secret-key-min-32-characters
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Google Earth Engine
GEE_SERVICE_ACCOUNT_KEY_PATH=/path/to/service-account-key.json
GEE_PROJECT_ID=your-gcp-project-id

# PME Weather API
PME_API_KEY=your-pme-api-key
PME_API_BASE_URL=https://api.pme.gov.sa

# SMTP (Alerts)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@saws.gov.sa
```

---

## API Documentation

### Base URL

```
http://localhost:8000/api/v1
```

### Core Endpoints

#### Fields

```
GET    /fields              # List fields (paginated, filtered)
GET    /fields/{id}         # Get field details
GET    /fields/stats        # Dashboard statistics
POST   /fields              # Create new field
PUT    /fields/{id}         # Update field
DELETE /fields/{id}         # Delete field
```

#### Satellite Data

```
GET    /satellite/sources   # Available satellites
GET    /satellite/images    # Available imagery
GET    /satellite/indices/{field_id}   # Vegetation indices
GET    /satellite/ndvi/{field_id}      # NDVI time series
```

#### Weather

```
GET    /weather/current     # Current conditions
GET    /weather/forecast    # 5-day forecast
GET    /weather/history     # Historical data
```

#### Drought

```
GET    /drought/status      # Current SPEI status
GET    /drought/forecast    # Drought prediction
GET    /drought/spei        # SPEI values by timescale
```

#### Alerts

```
GET    /alerts              # List alerts
POST   /alerts              # Create alert
PUT    /alerts/{id}/read    # Mark as read
WS     /ws/alerts           # Real-time alerts (WebSocket)
```

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Vegetation Indices

### Core Indices (Primary)

| Index | Formula | Range | Use |
|-------|---------|-------|-----|
| **NDVI** | (NIR - RED) / (NIR + RED) | -1 to 1 | Primary vegetation health |
| **EVI** | 2.5 × (NIR - RED) / (NIR + 6×RED - 7.5×BLUE + 1) | -1 to 1 | Dense canopy monitoring |
| **SAVI** | (NIR - RED) / (NIR + RED + L) × (1 + L) | -1 to 1 | Bright soil correction |
| **MSAVI** | (2×NIR + 1 - √((2×NIR+1)² - 8×(NIR-RED))) / 2 | -1 to 1 | Sparse vegetation |
| **OSAVI** | (NIR - RED) / (NIR + RED + 0.16) | -1 to 1 | Optimized soil adjustment |

### Drought Monitoring

| Index | Purpose | Lead Time |
|-------|---------|-----------|
| **NDMI** | Water stress detection | 1-2 weeks |
| **VHI** | Vegetation Health (WMO standard) | Real-time |
| **TCI** | Temperature Condition Index | Real-time |
| **SPEI** | Precipitation-evapotranspiration balance | 3-12 months |
| **SPI** | Standardized Precipitation Index | 1-24 months |

### Saudi-Specific Indices

| Index | Description | Target Crop |
|-------|-------------|-------------|
| **Arid NDVI** | Corrected for 30% sandy soil content | All EP crops |
| **Oasis Health Index** | Monitors traditional oasis ecosystems | Date palms |
| **Date Palm Health Index** | Combines NDVI, EVI, NDMI, canopy | 2M+ Al-Hasa palms |
| **Dust Storm Detection** | Shamal wind impact on LST & NDVI | All exposed crops |
| **Thermal Stress Index** | Crop-specific heat stress (45-50°C) | Summer crops |

### Advanced Indices

- **MCARI**: Modified Chlorophyll Absorption Ratio Index
- **MTVI2**: Modified Triangular Vegetation Index (2)
- **NDRE**: Normalized Difference Red Edge
- **CCI**: Canopy Chlorophyll Index
- **GNDVI**: Green NDVI
- **PRI**: Photochemical Reflectance Index
- **SIPI**: Structure Insensitive Pigment Index
- **ARI**: Anthocyanin Reflectance Index
- **Red Edge Indices**: CIred edge, NDVIred edge
- **Composite Indices**: VHI, DSI, CDVI

---

## Drought Monitoring

### SPEI Classification (WMO Standard)

| SPEI Value | Classification | Color Code | Action Required |
|------------|----------------|------------|-----------------|
| ≤ -2.5 | **Extreme Drought** | 🔴 Dark Red | Emergency measures, water rationing |
| -2.5 to -2.0 | **Severe Drought** | 🔴 Red | Critical water reduction |
| -2.0 to -1.5 | **Moderate Drought** | 🟠 Orange | Reduce usage, monitor crops |
| -1.5 to -1.0 | **Mild Drought** | 🟡 Yellow | Advisory, prepare contingency |
| -1.0 to -0.5 | **Abnormally Dry** | 🟢 Light Green | Monitor conditions |
| > -0.5 | **Normal** | 🟢 Green | No action |

### SPEI Timescales

- **SPEI-3**: Short-term conditions (recent months)
- **SPEI-6**: Medium-term conditions (seasonal)
- **SPEI-12**: Long-term conditions (annual)
- **SPEI-24**: Extended drought (multi-year)

### Saudi Crop-Specific NDVI Thresholds

| Crop | Excellent | Good | Moderate | Poor |
|------|-----------|------|----------|------|
| **Dates** | > 0.45 | 0.40-0.45 | 0.30-0.40 | < 0.30 |
| **Wheat** | > 0.35 | 0.30-0.35 | 0.25-0.30 | < 0.25 |
| **Tomatoes** | > 0.40 | 0.35-0.40 | 0.30-0.35 | < 0.30 |
| **Alfalfa** | > 0.45 | 0.40-0.45 | 0.35-0.40 | < 0.35 |
| **Sorghum** | > 0.35 | 0.30-0.35 | 0.25-0.30 | < 0.25 |
| **Citrus** | > 0.50 | 0.45-0.50 | 0.40-0.45 | < 0.40 |

---

## Geographic Coverage

### Eastern Province, Saudi Arabia

**Coordinate Bounds (EPSG:4326 / WGS84):**
- **Latitude**: 24.0°N to 28.0°N
- **Longitude**: 45.0°E to 55.0°E (extended to include Hafar Al-Batin district)

### Major Agricultural Districts

| District | Coordinates (minLon, minLat, maxLon, maxLat) | Key Features |
|----------|----------------------------------------------|--------------|
| **Al-Hasa** | 49.5°E, 25.0°N - 50.0°E, 26.0°N | 2M+ date palms, UNESCO heritage |
| **Qatif** | 50.0°E, 26.0°N - 50.5°E, 26.6°N | Coastal date farms |
| **Hofuf** | 49.3°E, 25.0°N - 49.8°E, 25.6°N | Historic agricultural center |
| **Dammam** | 50.0°E, 26.2°N - 50.5°E, 26.5°N | Urban agriculture |
| **Al-Khobar** | 50.2°E, 26.2°N - 50.5°E, 26.5°N | Peri-urban farms |
| **Al-Jubail** | 49.5°E, 26.8°N - 50.2°E, 27.2°N | Industrial zone agriculture |
| **Hafar Al-Batin** | 45.5°E, 27.5°N - 46.5°E, 28.5°N | Northern EP farms |

### Climate Profile

| Season | Daytime | Nighttime | Rainfall |
|--------|---------|-----------|----------|
| **Summer** (Jun-Aug) | 45-50°C | 30-35°C | < 5mm |
| **Winter** (Dec-Feb) | 20-25°C | 10-15°C | < 50mm |
| **Annual** | - | - | < 200mm |

**Dominant Winds**: Shamal (northwest) brings dust storms

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SAWS Architecture                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │   React 19   │    │   FastAPI    │    │  Google      │          │
│  │   Frontend   │◄──►│   Backend    │◄──►│  Earth       │          │
│  │  (TypeScript)│    │  (Python)    │    │  Engine      │          │
│  └──────────────┘    └──────┬───────┘    └──────────────┘          │
│                              │                                          │
│                     ┌────────┴────────┐                               │
│                     │  PostgreSQL +   │                               │
│                     │   PostGIS       │                               │
│                     │  TimescaleDB    │                               │
│                     │     Redis       │                               │
│                     └─────────────────┘                               │
│                                                                       │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │   Celery     │    │  WebSocket   │    │ TensorFlow   │          │
│  │  (Tasks)     │    │  (Real-time) │    │  Serving     │          │
│  └──────────────┘    └──────────────┘    └──────────────┘          │
└─────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
Satellite Imagery (NASA/ESA/USGS)
           │
           ▼
Google Earth Engine Processing
           │
           ▼
Vegetation Index Calculation (20+ indices)
           │
           ▼
PostgreSQL + PostGIS Storage
           │
           ▼
FastAPI REST API
           │
           ▼
React Frontend (Real-time updates via WebSocket)
```

### Background Tasks (CeleryBeat)

| Task | Schedule | Description |
|------|----------|-------------|
| `fetch_modis_data` | Daily | MODIS 16-day composite imagery |
| `fetch_landsat_data` | Daily | Landsat 8-9 imagery |
| `fetch_sentinel1_data` | Daily | Sentinel-1 SAR imagery |
| `fetch_current_weather` | Every 6 hours | PME weather data |
| `calculate_spei` | Every 12 hours | Drought index calculation |
| `generate_alerts` | Hourly | Alert processing |
| `send_notifications` | Every 15 minutes | Pending alert delivery |

---

## Saudi Government Compliance

### Data Localization (SDAIA)

- ✅ All data stored within Saudi borders
- ✅ SDAIA National Cloud or certified Tier III data centers
- ✅ No cross-border data transfer without approval

### Security Standards (NCA)

- ✅ AES-256 encryption at rest
- ✅ TLS 1.3 for data in transit
- ✅ Multi-factor authentication (MFA)
- ✅ 5-year log retention (NCA requirement)
- ✅ 72-hour breach notification (PDPL)

### Certifications

| Certification | Status | Timeline |
|---------------|--------|----------|
| **ISO 27001** | Planned | 6 months |
| **NCA ECC** | Planned | 3 months |
| **PDPL Compliance** | In Progress | 3 months |

---

## Contributing

This is a Saudi government project aligned with Vision 2030.

### For External Contributions

Please contact: **tech@saws.gov.sa**

### Development Guidelines

1. Follow Saudi coding standards
2. All code must pass security review
3. Documentation in Arabic and English
4. Adhere to PDPL data handling requirements

---

## License

Copyright © 2026 Saudi AgriDrought Warning System

Ministry of Environment, Water and Agriculture
Kingdom of Saudi Arabia

**Vision 2030 Food Security Program**

---

## Support

| Contact Type | Email | Phone |
|--------------|-------|-------|
| **Technical Support** | tech@saws.gov.sa | +966-13-XXX-XXXX |
| **General Inquiries** | info@saws.gov.sa | +966-13-XXX-XXXX |
| **Emergency Issues** | emergency@saws.gov.sa | 24/7 Hotline |

---

## Acknowledgments

### Satellite Data Providers
- **NASA MODIS**: Terra/Aqua satellites
- **ESA Sentinel**: Sentinel-1 (SAR), Sentinel-2 (MSI)
- **USGS Landsat**: Landsat 8-9 OLI

### Weather Data
- **Presidency of Meteorology & Environment (PME)**: Saudi Arabia

### Funding & Support
- **Saudi Vision 2030**: Food Security Program
- **Ministry of Environment, Water and Agriculture**
- **National Center for Palms & Dates**

---

<div align="center">

## **صانع القرار الذكي للزراعة في المملكة العربية السعودية**

*Smart Decision Maker for Agriculture in the Kingdom of Saudi Arabia*

**نظام الإنذار المبكر بالجفاف الزراعي - المنطقة الشرقية**

*Agricultural Drought Early Warning System - Eastern Province*

[![Vision 2030](https://img.shields.io/badge/Vision-2030-green.svg)](https://vision2030.gov.sa/)
[![MEWA](https://img.shields.io/badge/MEWA-Ministry-blue.svg)](https://mewa.gov.sa/)

</div>
