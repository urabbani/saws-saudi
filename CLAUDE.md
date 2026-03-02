# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Last Scientific Audit**: March 2026 - See [SCIENTIFIC_IMPROVEMENTS.md](docs/SCIENTIFIC_IMPROVEMENTS.md)

## Project Overview

**Saudi AgriDrought Warning System (SAWS)** is a full-stack agricultural drought monitoring platform for Saudi Arabia's Eastern Province. It provides GIS visualization, satellite data integration via Google Earth Engine, crop health monitoring, and real-time alerts for agricultural management.

**Current Status**: Production implementation with Python FastAPI backend, React frontend, PostgreSQL+PostGIS database, and comprehensive geospatial processing.

## Development Commands

### Frontend
```bash
# Install dependencies
npm install

# Start development server with HMR
npm run dev

# Build for production
npm run build

# Run ESLint
npm run lint

# Preview production build locally
npm run preview
```

### Backend
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements/dev.txt

# Initialize database
python scripts/init_db.py
python scripts/seed_data.py

# Run development server
uvicorn app.main:app --reload

# Run Celery worker
celery -A app.tasks worker --loglevel=info

# Run Celery beat (scheduler)
celery -A app.tasks beat --loglevel=info
```

## Technology Stack

### Frontend
- **React 19.2** with TypeScript
- **Vite 7.2** for fast development and HMR
- **Tailwind CSS** with custom desert theme design system
- **Shadcn/ui** (Radix UI primitives) - 50+ reusable components
- **Leaflet 1.9.4** + React Leaflet 5.0 for GIS mapping
- **Chart.js 4.5** + Recharts 2.15 for data visualization
- **React Query** (TanStack Query) for server state management
- **Sonner 2.0** for toast notifications
- **Axios 1.13** for HTTP client

### Backend
- **Python 3.12** with FastAPI 0.115
- **PostgreSQL** + **PostGIS** for geospatial data
- **TimescaleDB** for time-series optimization
- **Redis** for caching and Celery broker
- **Celery 5.4** for background task processing
- **SQLAlchemy 2.0** async ORM
- **Google Earth Engine** for satellite data processing
- **Alembic** for database migrations

## Project Structure

```
saws-saudi/
├── frontend/                      # React frontend
│   ├── src/
│   │   ├── components/ui/        # Shadcn/ui components (50+)
│   │   ├── sections/             # Dashboard sections
│   │   │   ├── Header.tsx
│   │   │   ├── DashboardOverview.tsx
│   │   │   ├── GISMap.tsx
│   │   │   ├── CropHealthMonitor.tsx
│   │   │   ├── SatelliteSources.tsx
│   │   │   ├── AlertsPanel.tsx
│   │   │   ├── WeatherWidget.tsx
│   │   │   ├── AnalyticsPanel.tsx
│   │   │   └── FieldDetailModal.tsx
│   │   ├── services/             # API client layer (NEW)
│   │   │   ├── api.ts             # Axios instance with interceptors
│   │   │   ├── fields.ts          # Field API calls
│   │   │   ├── satellite.ts       # Satellite data API
│   │   │   ├── weather.ts         # Weather API calls
│   │   │   ├── alerts.ts          # Alert API calls
│   │   │   └── websocket.ts       # WebSocket client
│   │   ├── hooks/                 # Custom React hooks (NEW)
│   │   │   ├── useFields.ts       # Field data fetching
│   │   │   ├── useWeather.ts      # Weather data fetching
│   │   │   ├── useAlerts.ts       # Alert management
│   │   │   └── useSatellite.ts    # Satellite imagery
│   │   ├── types/
│   │   │   └── index.ts            # TypeScript interfaces
│   │   ├── data/
│   │   │   └── mockData.ts         # Mock data for development
│   │   ├── lib/
│   │   │   └── utils.ts           # cn() utility function
│   │   ├── App.tsx                 # Main application with QueryClientProvider
│   │   └── main.tsx                # Entry point
│   └── package.json
│
├── backend/                       # Python backend (NEW)
│   ├── app/
│   │   ├── main.py                 # FastAPI application entry
│   │   ├── config.py              # Configuration management
│   │   ├── dependencies.py        # Dependency injection
│   │   ├── middleware.py          # CORS, logging, security headers
│   │   ├── api/v1/                # REST API endpoints
│   │   │   ├── fields.py          # Field CRUD endpoints
│   │   │   ├── satellite.py       # Satellite data endpoints
│   │   │   ├── weather.py         # Weather data endpoints
│   │   │   ├── alerts.py          # Alert management
│   │   │   ├── analytics.py       # Analytics endpoints
│   │   │   └── districts.py       # District data
│   │   ├── models/                 # SQLAlchemy models
│   │   │   ├── field.py            # Field with PostGIS geometry
│   │   │   ├── alert.py           # Alert model
│   │   │   ├── satellite.py        # Satellite data model
│   │   │   └── weather.py         # Weather data model
│   │   ├── schemas/                # Pydantic schemas
│   │   ├── services/              # Business logic
│   │   │   ├── satellite/          # Google Earth Engine integration
│   │   │   │   ├── gee.py         # GEE client with bounds validation
│   │   │   │   ├── modis.py       # MODIS data fetcher
│   │   │   │   ├── landsat.py     # Landsat data fetcher
│   │   │   │   └── indices.py      # 20+ vegetation indices
│   │   │   ├── weather/            # PME API client
│   │   │   ├── drought/           # SPEI calculation
│   │   │   │   ├── spei.py       # SPEI-3/6/12 calculation
│   │   │   │   └── classifier.py  # Drought classification
│   │   │   └── alert/             # Alert generation
│   │   │       ├── generator.py   # Alert logic
│   │   │       └── notifier.py    # Email/SMS/WhatsApp
│   │   ├── tasks/                # Celery background tasks
│   │   │   ├── satellite_fetch.py # Scheduled satellite data
│   │   │   ├── weather_fetch.py   # Scheduled weather data
│   │   │   ├── index_calculation.py # NDVI calculations
│   │   │   ├── drought_monitor.py # SPEI calculation
│   │   │   └── alert_generation.py # Alert processing
│   │   ├── db/                    # Database setup
│   │   │   └── base.py            # Async session factory
│   │   └── utils/                 # Utilities
│   │       ├── geo.py             # Geospatial utilities
│   │       ├── date.py            # Date/time utilities
│   │       └── logging.py         # Structured logging
│   ├── ml/                        # Machine Learning models
│   ├── etl/                       # Airflow data pipelines
│   ├── scripts/                   # Utility scripts
│   ├── requirements/              # Python dependencies
│   │   ├── base.txt               # Core dependencies
│   │   ├── geospatial.txt         # Geospatial libraries
│   │   ├── ml.txt                 # ML libraries
│   │   └── dev.txt                # Development dependencies
│   └── pyproject.toml             # Project configuration
│
└── docs/                          # Documentation
```

## Architecture

### Full-Stack Architecture

The system follows a modern frontend-backend separation:

**Frontend (React)**
- QueryClientProvider wraps App for React Query
- Services layer (`src/services/`) handles API communication
- Custom hooks (`src/hooks/`) provide data fetching with caching
- WebSocket client for real-time alerts

**Backend (FastAPI)**
- Async/await throughout for performance
- Dependency injection via `app.dependencies`
- Middleware for CORS, security, logging, errors
- Celery for scheduled background tasks

### API Communication

The frontend uses these service modules:
- `services/api.ts`: Axios instance with interceptors for auth and error handling
- `services/fields.ts`: Field CRUD operations
- `services/satellite.ts`: Satellite imagery and vegetation indices
- `services/weather.ts`: Current conditions and forecasts
- `services/alerts.ts`: Alert management
- `services/websocket.ts`: Real-time alert subscriptions

### Geospatial Architecture

**Coordinate System**: EPSG:4326 (WGS84) used throughout
- PostGIS: Geometry stored with SRID 4326
- Google Earth Engine: Explicit CRS transformation
- Leaflet: Default WGS84 projection

**Eastern Province Bounds** (Corrected - March 2026):
- Longitude: **45.0°E to 55.0°E** (extended from 49°E to include Hafar Al-Batin)
- Latitude: 24.0°N to 28.0°N
- Major Districts: Al-Hasa, Qatif, Hofuf, Dammam, Al-Khobar, Al-Jubail, Hafar Al-Batin

**Spatial Indexes**: All geometry columns have GiST indexes for performance

### State Management

**Frontend**:
- React Query manages server state with caching and invalidation
- Local state for UI (selectedField, activeTab, modals)
- Real-time alerts via WebSocket subscriptions

**Backend**:
- SQLAlchemy async sessions with automatic cleanup
- Redis for caching and Celery message broker
- Database connection pooling

### Type System

**TypeScript** (`src/types/index.ts`):
- `FieldData`: Field boundaries, crop info, NDVI, soil moisture, yield
- `Alert`: Severity (critical/warning/advisory/info), locations, timestamps
- `KPIData`: Metrics with trends, sparklines, status indicators
- `SatelliteSource`: MODIS, Sentinel-1/2, Landsat, Planet metadata
- `WeatherData`: Current conditions and forecasts
- `AnalyticsData`: Time series trends and predictions

**Python** (`backend/app/schemas/`):
- Pydantic v2 schemas for request/response validation
- `FieldCreate`, `FieldUpdate`, `FieldDetail` for field operations
- `AlertCreate`, `AlertUpdate` for alert management
- `VegetationIndexResponse` for satellite data

## Vegetation Indices

The system calculates 20+ vegetation indices for Saudi arid agriculture:

### Core Indices
- **NDVI**: Normalized Difference Vegetation Index (primary indicator)
- **EVI**: Enhanced Vegetation Index (reduces atmospheric effects)
- **SAVI**: Soil Adjusted Vegetation Index (for bright soils)
- **MSAVI**: Modified SAVI (for sparse vegetation)
- **OSAVI**: Optimized Soil Adjusted Vegetation Index

### Saudi-Specific Indices
- **Arid NDVI**: Corrected for sandy soils (30% sand content)
- **Oasis Health Index**: For date palm oases (Al-Hasa)
- **Date Palm Health Index**: Specialized for 2M+ date palms
- **Dust Storm Detection**: Shamal wind impact assessment
- **Thermal Stress Index**: Crop-specific heat stress (45-50°C threshold)

### Drought Monitoring
- **SPEI-3/6/12**: Standardized Precipitation Evapotranspiration Index
- **NDMI**: Normalized Difference Moisture Index (water stress)
- **VHI**: Vegetation Health Index (WMO standard)
- **TCI**: Temperature Condition Index

## Scientific Methodology

### SPEI Calculation (WMO Compliant)

The SPEI calculation follows Vicente-Serrano et al. (2010) methodology:

```python
# 1. Calculate monthly P-ET (precipitation minus evapotranspiration)
# 2. Sum over time scale (3, 6, 12 months)
# 3. Fit log-logistic distribution using L-moments
alpha, beta, gamma = fit_log_logistic_params(pet_series)

# 4. Transform to cumulative probability
probability = log_logistic_cdf(value, alpha, beta, gamma)

# 5. Convert to standard normal Z-score (this is SPEI)
spei = standard_normal_ppf(probability)
```

**Critical**: Do NOT use simple z-score normalization. SPEI must follow standard normal distribution (mean≈0, std≈1).

### Time-Series Analysis

**Anomaly Detection**:
- Z-score method with 2.5σ threshold (≈99% confidence)
- Moving window baseline for adaptive detection
- Severity classification: moderate (< 3.5σ) vs extreme (> 3.5σ)

**Change Point Detection**:
- Two-sample t-test for regime shifts
- Minimum 5-point windows for stability
- Significance level: α = 0.05

**Missing Data Imputation**:
- Linear interpolation (default)
- Seasonal adjustment for agricultural data
- Maximum gap: 16 days (MODIS cycle)

### Validation Requirements

All index calculations MUST include:
- `validate_index_value()`: Bounds checking, NaN/Inf detection
- `calculate_index_uncertainty()`: Error propagation, confidence intervals
- Quality flags: excellent/good/moderate/poor

## API Endpoints

### Fields
- `GET /api/v1/fields` - List all fields (with pagination, filters)
- `GET /api/v1/fields/{id}` - Get field details
- `GET /api/v1/fields/stats` - Field statistics for dashboard
- `POST /api/v1/fields` - Create new field
- `PUT /api/v1/fields/{id}` - Update field
- `DELETE /api/v1/fields/{id}` - Delete field

### Satellite Data
- `GET /api/v1/satellite/sources` - Available satellites
- `GET /api/v1/satellite/images` - Satellite imagery
- `GET /api/v1/satellite/indices/{field_id}` - Vegetation indices
- `GET /api/v1/satellite/ndvi/{field_id}` - NDVI time series

### Weather
- `GET /api/v1/weather/current` - Current conditions
- `GET /api/v1/weather/forecast` - Weather forecast
- `GET /api/v1/weather/history` - Historical data

### Drought
- `GET /api/v1/drought/status` - Current drought status (SPEI)
- `GET /api/v1/drought/forecast` - Drought prediction
- `GET /api/v1/analytics/trends` - Crop trends

### Alerts
- `GET /api/v1/alerts` - List alerts
- `POST /api/v1/alerts` - Create alert
- `PUT /api/v1/alerts/{id}/read` - Mark as read
- `WS /api/v1/ws/alerts` - Real-time alerts (WebSocket)

## Drought Monitoring

### SPEI Classification (WMO Standards)
| SPEI Value | Classification | Action |
|------------|----------------|--------|
| ≤ -2.5 | Extreme Drought | Emergency measures |
| -2.5 to -2.0 | Severe Drought | Water rationing |
| -2.0 to -1.5 | Moderate Drought | Reduce usage |
| -1.5 to -1.0 | Mild Drought | Monitor |
| > -1.0 | Normal | No action |

### Saudi Crop-Specific Thresholds (Updated - March 2026)

| Crop | Excellent | Good | Moderate | Poor |
|------|-----------|------|----------|------|
| **Dates** | > 0.50 | > 0.40 | > 0.35 | < 0.30 |
| **Wheat** | > 0.45 | > 0.35 | > 0.30 | < 0.25 |
| **Tomatoes** | > 0.50 | > 0.40 | > 0.35 | < 0.30 |
| **Alfalfa** | > 0.55 | > 0.45 | > 0.40 | < 0.35 |
| **Sorghum** | > 0.35 | > 0.30 | > 0.25 | < 0.25 |
| **Citrus** | > 0.50 | > 0.45 | > 0.40 | < 0.40 |

**Phenology-Aware Classification**: Thresholds adjust based on crop growth stage

## Background Tasks

CeleryBeat schedules:
- **fetch_modis_data**: Daily - MODIS imagery (250m, 16-day composite)
- **fetch_landsat_data**: Daily - Landsat imagery (30m, 16-day)
- **fetch_current_weather**: 6 hours - PME weather data
- **calculate_spei**: 12 hours - Drought index calculation
- **generate_alerts**: Hourly - Alert processing
- **send_notifications**: 15 min - Pending alerts

## Saudi Government Compliance

- **Data Localization**: All data in Saudi data centers
- **Security**: AES-256, TLS 1.3, MFA required
- **Certifications**: ISO 27001, NCA ECC, PDPL compliance
- **Hosting**: SDAIA National Cloud or Tier III centers
- **Log Retention**: 5 years (NCA requirement)

## Path Aliases

The `@/` alias maps to `src/` (configured in `tsconfig.app.json` and `vite.config.ts`).

Example imports:
```typescript
import { Button } from '@/components/ui/button';
import { listFields } from '@/services/fields';
import { useFields } from '@/hooks/useFields';
import type { FieldData } from '@/types';
```

## GIS/Map Integration

The map uses React Leaflet with:
- Field polygons rendered from GeoJSON coordinates
- Multiple base layers (OSM, Satellite, Terrain)
- Data layer toggles (NDVI, crop types, soil moisture, temperature)
- Click interactions to open field detail modals
- Custom marker icons using Leaflet's `L.divIcon`

**Leaflet CSS imports** in `main.tsx`:
```typescript
import 'leaflet/dist/leaflet.css';
import 'leaflet-draw/dist/leaflet.draw.css';
```

## Styling Guidelines

### Tailwind CSS Conventions
- Use utility classes for all styling
- Responsive design with mobile-first approach (`sm:`, `md:`, `lg:`, `xl:`)
- Custom colors in `tailwind.config.js`: desert gold, wheat yellow, tomato red
- Use `cn()` utility from `lib/utils.ts` for conditional classes

### Component Pattern
```typescript
import { cn } from '@/lib/utils';

interface ComponentProps {
  variant?: 'default' | 'outline' | 'ghost';
  className?: string;
}

export function Component({ variant, className, ...props }: ComponentProps) {
  return (
    <div className={cn('base-classes', variant === 'outline' && 'outline-classes', className)} {...props} />
  );
}
```

## Toast Notifications

Using Sonner:
```typescript
import { toast } from 'sonner';

toast.success('Data saved successfully');
toast.error('Failed to load data');
toast.warning('Alert generated');
```

## Environment Variables

Frontend (`.env`):
```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/api/v1/ws/alerts
```

Backend (`.env`):
```bash
DB_HOST=localhost
DB_PORT=5432
DB_USER=saws_user
DB_PASSWORD=saws_password
DB_NAME=saws_db
REDIS_HOST=localhost
REDIS_PORT=6379
SECRET_KEY=change-this-in-production-min-32-characters
GEE_SERVICE_ACCOUNT_KEY_PATH=/path/to/key.json
PME_API_KEY=your-pme-api-key
```

## Important Notes

### Backend
- All database operations use async/await
- Geometry stored as PostGIS with SRID 4326, serialized to GeoJSON for APIs
- Spatial indexes automatically created on geometry columns
- Bounds validation for all geometries against Eastern Province limits
- Saudi-specific thresholds applied for all vegetation indices

### Frontend
- React Query provides caching (5 min default) and automatic refetching
- WebSocket automatically connects for real-time alerts
- API errors automatically display toast notifications
- Mock data available in `src/data/mockData.ts` for development

### Geospatial
- All coordinates in EPSG:4326 (WGS84)
- UTM Zone 38N recommended for spatial analysis
- Cloud cover limits: 40% for MODIS, 60% for Landsat (dust-adjusted)
- Bounds validation prevents invalid geometries

## Common Patterns

### Creating New API Endpoint
1. Add Pydantic schema in `app/schemas/`
2. Create endpoint in `app/api/v1/`
3. Add CRUD operations in `app/db/crud.py` if needed
4. Register router in `app/main.py`

### Creating New React Hook
1. Create hook in `src/hooks/use[Name].ts`
2. Use `useQuery` from `@tanstack/react-query`
3. Add query keys pattern for cache management
4. Export from `src/hooks/index.ts`

### Adding Vegetation Index
1. Add function to `app/services/satellite/indices.py`
2. Follow naming: `calculate_[index_name]()`
3. Add docstring with formula and range
4. Export from `__init__.py`

## Date Reference

Current date: March 2026

## Saudi Eastern Province

**Geographic Coverage**:
- Coastal cities: Dammam, Al-Khobar, Dhahran, Qatif
- Interior oases: Al-Hasa (2M+ date palms), Hofuf
- Industrial: Al-Jubail
- Northern: Hafar Al-Batin

**Climate**: Hyper-arid to arid
- Summer: 45-50°C daytime, 30-35°C nighttime
- Winter: 20-25°C daytime, 10-15°C nighttime
- Rainfall: <200mm annually
- Dominant winds: Shamal (northwest) dust storms

**Major Crops**:
- Dates: Al-Hasa oasis (50% national production)
- Wheat: Winter cereals
- Tomatoes: Protected cultivation
- Alfalfa: Year-round with irrigation
- Citrus: Coastal areas

## OpenCode Delegation

OpenCode is available for delegating coding tasks.

**Configuration:**
- Binary: `/home/umair/.opencode/bin/opencode`
- Model: `ollama/qwen3-coder-next:q4_K_M`
- Wrapper: `~/.local/bin/opencode-delegate`

**Usage:**
```bash
opencode-delegate "<detailed task description>"
```

**When to use:**
- Complex refactoring tasks
- Multi-file changes
- Autonomous code generation requiring file system access
