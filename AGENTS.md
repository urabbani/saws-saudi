# AGENTS.md

This file provides guidance for delegating tasks to specialized AI agents working on this repository.

**Last Scientific Audit**: March 2026 - See [SCIENTIFIC_IMPROVEMENTS.md](docs/SCIENTIFIC_IMPROVEMENTS.md)

---

## Project Overview

**Saudi AgriDrought Warning System (SAWS)** is a full-stack agricultural drought monitoring platform for Saudi Arabia's Eastern Province.

**Key Scientific Components**:
- WMO-compliant SPEI calculation (log-logistic distribution)
- Crop-specific NDVI thresholds for Saudi agriculture
- Time-series anomaly detection (Statistical Process Control)
- FAO-56 Penman-Monteith evapotranspiration
- Google Earth Engine satellite data processing

---

## Scientific Agent Capabilities

### Available Scientific Skills

The following specialized skills are available for scientific work:

| Skill | Purpose | When to Use |
|-------|---------|-------------|
| `claude-scientific-skills` | Comprehensive scientific audit | Validating methodology, reviewing calculations |
| `scientific-writing` | Documentation and papers | Writing scientific reports, documentation |
| `scientific-slides` | Presentation creation | Creating scientific presentations |
| `statistical-analysis` | Data analysis | Analyzing time-series data, validation |
| `research-lookup` | Literature review | Finding scientific references |
| `geopandas` | Spatial analysis | PostGIS operations, spatial queries |
| `seaborn` / `matplotlib` | Data visualization | Creating scientific plots |
| `scikit-learn` | ML for agriculture | Crop prediction, classification |

---

## Delegation Guidelines

### When to Delegate to Scientific Agents

1. **Scientific Validation**: Before implementing new indices or algorithms
2. **Literature Review**: When adding new scientific methods
3. **Data Analysis**: When validating historical data
4. **Documentation**: When writing scientific documentation

### When NOT to Delegate

1. **Simple CRUD operations**: Use standard coding patterns
2. **UI Components**: Use frontend development skills
3. **Configuration changes**: Direct editing is faster
4. **Bug fixes**: Direct debugging is more efficient

---

## Task Delegation Examples

### Example 1: Validating SPEI Calculation

```bash
# Delegate to scientific skill for validation
skill: claude-scientific-skills
task: "Review the SPEI calculation in backend/app/services/drought/spei.py
       to ensure it follows Vicente-Serrano et al. (2010) methodology.
       Verify that log-logistic distribution parameters are correctly estimated."
```

### Example 2: Adding New Vegetation Index

```bash
# Step 1: Use research skill to find methodology
skill: research-lookup
task: "Find scientific literature on Red Edge Chlorophyll Index
       for drought monitoring in arid regions."

# Step 2: Implement using coding agent
# (direct implementation based on research)

# Step 3: Validate with scientific skill
skill: claude-scientific-skills
task: "Validate the new Red Edge index implementation against
       established formulas and ranges."
```

### Example 3: Time-Series Analysis

```bash
# Delegate to statistical analysis skill
skill: statistical-analysis
task: "Analyze 5 years of NDVI data for Al-Hasa date palms.
       Detect trends, anomalies, and change points using
       the methods in anomaly_detection.py."
```

---

## Critical Scientific Constraints

### SPEI Calculation (DO NOT DELEGATE TO NON-SCIENTIFIC AGENTS)

The SPEI calculation has specific scientific requirements:

```python
# REQUIRED METHOD (March 2026)
alpha, beta, gamma = fit_log_logistic_params(pet_array)
probability = log_logistic_cdf(latest_pet, alpha, beta, gamma)
spei_value = standard_normal_ppf(probability)

# FORBIDDEN METHOD
# spei = (value - mean) / std  # This is NOT valid SPEI
```

**Validation Required**:
- Mean of SPEI series ≈ 0
- Standard deviation ≈ 1
- No values outside ±6 (extreme outliers)

### Crop-Specific Thresholds

Different crops have different NDVI thresholds:

| Crop | Excellent | Good | Moderate | Poor |
|------|-----------|------|----------|------|
| Dates | > 0.50 | > 0.40 | > 0.35 | < 0.30 |
| Wheat | > 0.45 | > 0.35 | > 0.30 | < 0.25 |
| Tomatoes | > 0.50 | > 0.40 | > 0.35 | < 0.30 |
| Alfalfa | > 0.55 | > 0.45 | > 0.40 | < 0.35 |

**Never use generic thresholds** for Saudi crops.

### Geographic Bounds

Eastern Province bounds were corrected in March 2026:

```python
# CORRECT (includes Hafar Al-Batin)
eastern_province_bounds = (45.0, 24.0, 55.0, 28.0)

# INCORRECT (excludes Hafar Al-Batin)
eastern_province_bounds = (49.0, 24.0, 55.0, 28.0)
```

---

## File-Specific Delegation

### High-Scientific-Complexity Files (Use Scientific Agents)

| File | Complexity | Recommended Agent |
|------|------------|-------------------|
| `spei.py` | High | claude-scientific-skills |
| `classifier.py` | High | claude-scientific-skills |
| `evapotranspiration.py` | High | claude-scientific-skills |
| `anomaly_detection.py` | Medium | statistical-analysis |
| `indices.py` | Medium | claude-scientific-skills |

### Low-Scientific-Complexity Files (Direct Coding)

| File | Complexity | Approach |
|------|------------|----------|
| `gee.py` | Low | Direct implementation |
| `modis.py` | Low | Direct implementation |
| `landsat.py` | Low | Direct implementation |
| `pme.py` | Low | Direct implementation |
| API routes | Low | Direct implementation |

---

## Development Environment

### WSL/Windows Filesystem Workarounds

The project is hosted on WSL filesystem (`/mnt/d/saws-saudi`), which requires specific workarounds:

**Frontend**:
```bash
# Use --no-bin-links to avoid symlink errors on Windows filesystem
npm install --no-bin-links

# Start dev server with direct node execution
node node_modules/vite/bin/vite.js --host 0.0.0.0 --port 3000
```

**Backend**:
```bash
# Use system Python with --user flag (venv doesn't work well on /mnt/d/)
pip install --user -r requirements/base.txt
pip install --user orjson  # Required for ORJSONResponse

# Start server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Server URLs**:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## OpenCode Delegation

For autonomous multi-file tasks, OpenCode is available:

```bash
# Configuration
Binary: /home/umair/.opencode/bin/opencode
Model: ollama/qwen3-coder-next:q4_K_M
Wrapper: ~/.local/bin/opencode-delegate

# Usage
opencode-delegate "<detailed task description>"

# Example
opencode-delegate "Refactor the drought classification system
                   to use the new crop-specific thresholds in
                   backend/app/services/drought/classifier.py"
```

**When to use OpenCode**:
- Multi-file refactoring
- Autonomous code generation
- Complex file system operations
- When delegation is more efficient than direct coding

**When NOT to use OpenCode**:
- Simple one-file changes
- Scientific validation (use claude-scientific-skills)
- Quick bug fixes

---

## Validation Checklist

Before considering any scientific implementation complete:

### SPEI Calculation
- [ ] Uses log-logistic distribution (not simple z-score)
- [ ] L-moments parameter estimation
- [ ] Standard normal transformation
- [ ] Validation passes (mean≈0, std≈1)

### Vegetation Indices
- [ ] Formula documented with references
- [ ] Range validation implemented
- [ ] Uncertainty quantification included
- [ ] Saudi-specific corrections applied

### Drought Classification
- [ ] Crop-specific thresholds used
- [ ] Phenology-aware interpretation
- [ ] WMO standard classification
- [ ] Multi-indicator approach

### Time-Series Analysis
- [ ] Appropriate method selected (z-score, change point, etc.)
- [ ] Significance level specified (α = 0.05 default)
- [ ] Confidence intervals provided
- [ ] Agricultural context considered

---

## References for Agents

When delegating scientific tasks, provide these references:

### Primary References
1. Vicente-Serrano, S. M., et al. (2010). "A Multiscalar Drought Index Sensitive to Global Warming: The Standardized Precipitation Evapotranspiration Index." *Journal of Climate*, 23(7), 1696-1718.

2. WMO & GWP (2016). *Handbook of Drought Indicators and Indices*. World Meteorological Organization.

3. Allen, R. G., et al. (1998). *Crop Evapotranspiration - Guidelines for Computing Crop Water Requirements - FAO Irrigation and Drainage Paper 56*. FAO.

### Saudi-Specific References
4. Al-Bakri, J. T., et al. (2011). "Date Palm Water Requirements in the Eastern Province of Saudi Arabia." *3rd International Date Palm Conference*, Riyadh.

5. Saudi Ministry of Agriculture (2020). *Crop Calendar Guidelines for Eastern Province*. Riyadh.

---

## Contact

For questions about scientific methodology or agent delegation:
- Technical: tech@saws.gov.sa
- Scientific: science@saws.gov.sa
