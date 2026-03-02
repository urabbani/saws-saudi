# GEMINI.md

This file provides guidance to Google Gemini when working with code in this repository.

**Last Scientific Audit**: March 2026 - See [SCIENTIFIC_IMPROVEMENTS.md](docs/SCIENTIFIC_IMPROVEMENTS.md)

---

## Project Overview

**Saudi AgriDrought Warning System (SAWS)** is a full-stack agricultural drought monitoring platform for Saudi Arabia's Eastern Province. It provides GIS visualization, **Google Earth Engine** satellite data processing, crop health monitoring, and real-time alerts for agricultural management.

**Current Status**: Production implementation with Python FastAPI backend, React frontend, PostgreSQL+PostGIS database, and comprehensive geospatial processing.

---

## Google Earth Engine Integration

### GEE Configuration

The system uses Google Earth Engine for satellite data processing:

```python
# Service account authentication
import ee

ee.Initialize(credentials=ee.ServiceAccountCredentials(
    email=os.getenv('GEE_SERVICE_ACCOUNT_EMAIL'),
    key_file=os.getenv('GEE_SERVICE_ACCOUNT_KEY_PATH')
))
```

### GEE Best Practices

1. **Bounds Validation**: All Earth Engine queries MUST validate against Eastern Province bounds
   ```python
   eastern_province_bounds = ee.Geometry.Rectangle([
       45.0, 24.0,  # West, South (extended to include Hafar Al-Batin)
       55.0, 28.0   # East, North
   ])
   ```

2. **CRS Transformation**: Explicitly set coordinate system
   ```python
   image = image.reproject(crs='EPSG:4326', scale=250)
   ```

3. **Cloud Filtering**: Apply quality masks before computation
   ```python
   qa = image.select('QA')
   cloud_mask = qa.bitwiseAnd(1 << 10).eq(0)
   ```

### Satellite Collections

| Collection | ID | Resolution | Use |
|------------|-----|------------|-----|
| MODIS NDVI | `MODIS/006/MOD13Q1` | 250m | 16-day composite |
| Landsat 8 | `LANDSAT/LC08/C02/T1_L2` | 30m | Surface reflectance |
| Sentinel-2 | `COPERNICUS/S2_SR_HARMONIZED` | 10m | High-res analysis |

---

## Scientific Methodology (March 2026 Updates)

### SPEI Calculation

**IMPORTANT**: The SPEI calculation was updated in March 2026 to use proper log-logistic distribution fitting (Vicente-Serrano et al., 2010).

```python
# CORRECT implementation (spei.py)
alpha, beta, gamma = fit_log_logistic_params(pet_array)
probability = log_logistic_cdf(latest_pet, alpha, beta, gamma)
spei_value = standard_normal_ppf(probability)

# INCORRECT (old method - DO NOT USE)
# spei = (value - mean) / std  # This is NOT valid SPEI
```

### Crop-Specific NDVI Thresholds

All NDVI classification MUST use crop-specific thresholds:

```python
# For Date Palms
if ndvi > 0.50: return "excellent"
elif ndvi > 0.40: return "good"
elif ndvi > 0.35: return "moderate"
else: return "poor"

# For Wheat (different thresholds!)
if ndvi > 0.45: return "excellent"
elif ndvi > 0.35: return "good"
elif ndvi > 0.30: return "moderate"
else: return "poor"
```

### Validation Requirements

All index calculations must include validation:

```python
from backend.app.services.satellite.indices import validate_index_value

result = validate_index_value("NDVI", ndvi_value, satellite_source="modis")
# Returns: {valid: bool, quality: str, warnings: [], bounds: {...}}
```

---

## Development Commands

### Frontend
```bash
npm install
npm run dev
npm run build
```

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements/dev.txt
uvicorn app.main:app --reload
```

---

## Technology Stack

### Frontend
- **React 19.2** with TypeScript
- **Vite 7.2** for fast development and HMR
- **Tailwind CSS** with custom desert theme
- **Leaflet 1.9.4** + React Leaflet 5.0 for GIS mapping
- **React Query** for server state management

### Backend
- **Python 3.12** with FastAPI 0.115
- **PostgreSQL** + **PostGIS** for geospatial data
- **TimescaleDB** for time-series optimization
- **Google Earth Engine** for satellite processing
- **SQLAlchemy 2.0** async ORM

---

## API Endpoints

### Drought
```
GET /api/v1/drought/status      # Current SPEI status (WMO compliant)
GET /api/v1/drought/forecast    # Drought prediction
GET /api/v1/anomaly/{field_id}  # Time-series anomaly detection
GET /api/v1/trend/{field_id}    # Trend analysis
```

### Satellite
```
GET /api/v1/satellite/indices/{field_id}  # Vegetation indices with validation
GET /api/v1/satellite/ndvi/{field_id}     # NDVI time series
```

---

## Saudi Eastern Province

### Geographic Coverage (Corrected - March 2026)
- **Longitude**: 45.0°E to 55.0°E (was 49°E, extended to include Hafar Al-Batin)
- **Latitude**: 24.0°N to 28.0°N

### Climate
- **Summer**: 45-50°C daytime, 30-35°C nighttime
- **Winter**: 20-25°C daytime, 10-15°C nighttime
- **Rainfall**: <200mm annually (hyper-arid)
- **Dominant Winds**: Shamal (northwest) dust storms

### Major Crops
- **Dates**: Al-Hasa oasis (2M+ palms, 50% national production)
- **Wheat**: Winter cereals (Nov-Jun)
- **Tomatoes**: Protected cultivation
- **Alfalfa**: Year-round with irrigation
- **Citrus**: Coastal areas

---

## File Structure (Key Files)

```
backend/app/services/
├── satellite/
│   ├── gee.py              # Google Earth Engine client
│   ├── indices.py          # 20+ vegetation indices (with validation)
│   ├── modis.py            # MODIS data fetcher
│   └── landsat.py          # Landsat data fetcher
├── drought/
│   ├── spei.py             # SPEI calculation (log-logistic method)
│   └── classifier.py       # Crop-specific drought classification
├── anomaly_detection.py    # NEW: Time-series analysis (400+ lines)
└── evapotranspiration.py   # NEW: FAO-56 ET calculation (600+ lines)
```

---

## Important Notes

### GEE-Specific
- Always use `ee.Number()` for numeric operations in Earth Engine
- Filter collections by date AND bounds before processing
- Use `getInfo()` sparingly - prefer client-side mapping
- Monitor quota usage (computation vs. storage)

### Scientific Accuracy
- SPEI values must follow standard normal distribution (mean≈0, std≈1)
- Use `validate_spei_series()` after calculation
- All NDVI thresholds are crop-specific
- Phenology stage affects interpretation

### Saudi Adaptations
- Dust storm adjustment: +20% cloud cover tolerance
- Sandy soil correction: 30% sand content for NDVI
- Summer ET adjustment: +30% for 45-50°C conditions
- Shamal wind impact on LST and NDVI

---

## References

- Vicente-Serrano et al. (2010) - SPEI methodology
- WMO & GWP (2016) - Drought monitoring handbook
- FAO-56 (Allen et al., 1998) - Evapotranspiration
- Al-Bakri et al. (2011) - Saudi date palm research
