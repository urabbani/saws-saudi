import type { 
  KPIData, 
  CropType, 
  SatelliteSource, 
  Alert, 
  FieldData, 
  DistrictData, 
  WeatherData,
  VegetationIndex,
  AnalyticsData
} from '@/types';

// KPI Cards Data
export const kpiData: KPIData[] = [
  {
    id: 'cultivated-area',
    title: 'Total Cultivated Area',
    value: '2.84M',
    unit: 'hectares',
    trend: 3.2,
    trendLabel: 'from last season',
    icon: 'Map',
    sparklineData: [2.65, 2.68, 2.72, 2.75, 2.78, 2.81, 2.84],
    status: 'positive'
  },
  {
    id: 'crop-health',
    title: 'Active Crop Health Index',
    value: '78.4',
    unit: '/100',
    trend: -2.1,
    trendLabel: 'moderate concern',
    icon: 'Heart',
    sparklineData: [82, 81, 80, 79, 78, 78, 78.4],
    status: 'warning'
  },
  {
    id: 'water-stress',
    title: 'Water Stress Alerts',
    value: '127',
    unit: 'fields',
    trend: 15,
    trendLabel: 'new this week',
    icon: 'Droplets',
    sparklineData: [95, 102, 108, 115, 120, 124, 127],
    status: 'negative'
  },
  {
    id: 'ndvi-coverage',
    title: 'NDVI Coverage (Latest)',
    value: '94.2',
    unit: '%',
    trend: 0,
    trendLabel: 'updated 6h ago',
    icon: 'Satellite',
    sparklineData: [89, 90, 91, 92, 93, 93.5, 94.2],
    status: 'positive'
  }
];

// Crop Types Data
export const cropTypes: CropType[] = [
  {
    id: 'dates',
    name: 'Dates',
    color: '#d4a574',
    area: 985000,
    healthScore: 82,
    trend: 2.5
  },
  {
    id: 'wheat',
    name: 'Wheat',
    color: '#eab308',
    area: 520000,
    healthScore: 71,
    trend: -1.8
  },
  {
    id: 'tomatoes',
    name: 'Tomatoes',
    color: '#ef4444',
    area: 280000,
    healthScore: 75,
    trend: 3.2
  },
  {
    id: 'alfalfa',
    name: 'Alfalfa',
    color: '#86efac',
    area: 355000,
    healthScore: 89,
    trend: 1.5
  }
];

// Satellite Data Sources
export const satelliteSources: SatelliteSource[] = [
  {
    id: 'modis',
    name: 'MODIS (Terra/Aqua)',
    resolution: '250m - 1km',
    revisitTime: 'Daily',
    status: 'active',
    lastUpdate: '4 hours ago',
    description: 'Moderate Resolution Imaging Spectroradiometer aboard NASA satellites',
    useCases: ['Broad screening', 'Land Surface Temperature', 'Phenology tracking', 'Drought detection'],
    icon: 'Globe'
  },
  {
    id: 'sentinel-1',
    name: 'Sentinel-1 (SAR)',
    resolution: '~10m',
    revisitTime: '6-12 days',
    status: 'active',
    lastUpdate: '2 days ago',
    description: 'C-band Synthetic Aperture Radar for all-weather monitoring',
    useCases: ['All-weather monitoring', 'Soil moisture', 'Flood detection', 'Crop structure'],
    icon: 'Radar'
  },
  {
    id: 'sentinel-2',
    name: 'Sentinel-2 (Optical)',
    resolution: '10m',
    revisitTime: '5 days',
    status: 'active',
    lastUpdate: '1 day ago',
    description: 'High-resolution multispectral optical imagery',
    useCases: ['NDVI calculation', 'Crop classification', 'Stress detection', 'Chlorophyll assessment'],
    icon: 'Scan'
  },
  {
    id: 'landsat',
    name: 'Landsat 8/9',
    resolution: '30m',
    revisitTime: '8 days',
    status: 'active',
    lastUpdate: '3 days ago',
    description: 'Long-running Earth observation program with thermal bands',
    useCases: ['Historical analysis', 'Thermal imaging', 'Trend analysis', 'Water stress'],
    icon: 'Telescope'
  },
  {
    id: 'planet',
    name: 'Planet.com',
    resolution: '~3m',
    revisitTime: 'Daily',
    status: 'active',
    lastUpdate: '12 hours ago',
    description: 'High-resolution daily imagery from Dove constellation',
    useCases: ['Field-level detail', 'Rapid change detection', 'Validation', 'Precision agriculture'],
    icon: 'Orbit'
  }
];

// Alerts Data
export const alerts: Alert[] = [
  {
    id: '1',
    user_id: 'user-1',
    field_id: 'field-001',
    severity: 'critical',
    alert_type: 'drought',
    title: 'High Water Stress Detected',
    message: 'NDVI drop >20% observed in date palm plantations. Immediate irrigation recommended.',
    district: 'Dammam, Al Hamra District',
    priority: 90,
    data: { ndvi_drop: 0.23, crop_type: 'Dates' },
    is_read: false,
    read_at: undefined,
    email_sent: true,
    sms_sent: true,
    whatsapp_sent: false,
    created_at: '2025-01-26T14:30:00Z',
    expires_at: undefined
  },
  {
    id: '2',
    user_id: 'user-1',
    field_id: 'field-002',
    severity: 'critical',
    alert_type: 'low_ndvi',
    title: 'Severe NDVI Decline',
    message: 'Tomato greenhouses showing significant vegetation stress. Check irrigation systems.',
    district: 'Al Hofuf, Al-Ahsa Oasis',
    priority: 85,
    data: { ndvi: 0.25, threshold: 0.35, crop_type: 'Tomatoes' },
    is_read: false,
    read_at: undefined,
    email_sent: true,
    sms_sent: false,
    whatsapp_sent: false,
    created_at: '2025-01-26T10:15:00Z',
    expires_at: undefined
  },
  {
    id: '3',
    user_id: 'user-1',
    field_id: 'field-003',
    severity: 'warning',
    alert_type: 'soil_moisture',
    title: 'Moderate Drought Conditions',
    message: 'Soil moisture levels below threshold in northern regions.',
    district: 'Al Jubail, Industrial Zone',
    priority: 70,
    data: { soil_moisture: 15, threshold: 25 },
    is_read: true,
    read_at: '2025-01-25T17:00:00Z',
    email_sent: true,
    sms_sent: false,
    whatsapp_sent: false,
    created_at: '2025-01-25T16:45:00Z',
    expires_at: undefined
  },
  {
    id: '4',
    user_id: 'user-1',
    field_id: 'field-004',
    severity: 'advisory',
    alert_type: 'irrigation_needed',
    title: 'Soil Salinity Increase',
    message: '8 fields showing elevated salinity indices. Recommend soil testing.',
    district: 'Qatif, Coastal Area',
    priority: 60,
    data: { affected_fields: 8, salinity_index: 'elevated' },
    is_read: true,
    read_at: '2025-01-25T10:00:00Z',
    email_sent: true,
    sms_sent: false,
    whatsapp_sent: false,
    created_at: '2025-01-25T09:20:00Z',
    expires_at: undefined
  },
  {
    id: '5',
    user_id: 'user-1',
    field_id: undefined,
    severity: 'info',
    alert_type: 'harvest_ready',
    title: 'New Imagery Available',
    message: 'Fresh Sentinel-2 imagery covering entire province now available.',
    district: 'Eastern Province',
    priority: 10,
    data: { satellite: 'Sentinel-2', coverage: 'full_province' },
    is_read: true,
    read_at: '2025-01-26T08:30:00Z',
    email_sent: false,
    sms_sent: false,
    whatsapp_sent: false,
    created_at: '2025-01-26T08:00:00Z',
    expires_at: undefined
  },
  {
    id: '6',
    user_id: 'user-1',
    field_id: undefined,
    severity: 'info',
    alert_type: 'harvest_ready',
    title: 'Wheat Harvest Season Approaching',
    message: 'Coastal districts entering optimal harvest window.',
    district: 'Dammam, Al Khobar',
    priority: 30,
    data: { crop: 'wheat', districts: ['Dammam', 'Al Khobar'] },
    is_read: true,
    read_at: '2025-01-24T12:00:00Z',
    email_sent: false,
    sms_sent: false,
    whatsapp_sent: false,
    created_at: '2025-01-24T11:00:00Z',
    expires_at: undefined
  }
];

// Sample Field Data
export const sampleFields: FieldData[] = [
  {
    id: 'field-001',
    name: 'Field DAM-2847',
    coordinates: [
      [26.4180, 50.0800],
      [26.4200, 50.0800],
      [26.4200, 50.0830],
      [26.4180, 50.0830]
    ],
    center: [26.4190, 50.0815],
    area: 12.5,
    cropType: 'Dates',
    ndvi: 0.72,
    healthStatus: 'moderate',
    plantingDate: '2024-11-15',
    expectedHarvest: '2025-09-20',
    yieldEstimate: 4.2,
    waterStressIndex: 0.35,
    soilMoisture: 42,
    history: generateNDVIHistory()
  },
  {
    id: 'field-002',
    name: 'Field HOF-1932',
    coordinates: [
      [25.3530, 49.5830],
      [25.3550, 49.5830],
      [25.3550, 49.5850],
      [25.3530, 49.5850]
    ],
    center: [25.3540, 49.5840],
    area: 18.3,
    cropType: 'Wheat',
    ndvi: 0.45,
    healthStatus: 'stressed',
    plantingDate: '2024-11-10',
    expectedHarvest: '2025-04-15',
    yieldEstimate: 3.1,
    waterStressIndex: 0.22,
    soilMoisture: 28,
    history: generateNDVIHistory()
  },
  {
    id: 'field-003',
    name: 'Field JUB-4521',
    coordinates: [
      [26.9880, 49.6580],
      [26.9900, 49.6580],
      [26.9900, 49.6600],
      [26.9880, 49.6600]
    ],
    center: [26.9890, 49.6590],
    area: 25.7,
    cropType: 'Alfalfa',
    ndvi: 0.85,
    healthStatus: 'healthy',
    plantingDate: '2024-10-01',
    expectedHarvest: '2025-06-01',
    yieldEstimate: 78.5,
    waterStressIndex: 0.78,
    soilMoisture: 65,
    history: generateNDVIHistory()
  },
  {
    id: 'field-004',
    name: 'Field QAT-7823',
    coordinates: [
      [26.5080, 50.0480],
      [26.5100, 50.0480],
      [26.5100, 50.0500],
      [26.5080, 50.0500]
    ],
    center: [26.5090, 50.0490],
    area: 15.2,
    cropType: 'Tomatoes',
    ndvi: 0.58,
    healthStatus: 'moderate',
    plantingDate: '2024-12-01',
    expectedHarvest: '2025-04-30',
    yieldEstimate: 2.8,
    waterStressIndex: 0.48,
    soilMoisture: 38,
    history: generateNDVIHistory()
  }
];

// Generate NDVI history for charts
function generateNDVIHistory(): { date: string; ndvi: number; evi: number; ndwi: number }[] {
  const history = [];
  const baseDate = new Date('2024-11-01');
  
  for (let i = 0; i < 90; i += 5) {
    const date = new Date(baseDate);
    date.setDate(date.getDate() + i);
    
    // Simulate seasonal NDVI curve
    const dayOfYear = i;
    const seasonalFactor = Math.sin((dayOfYear / 180) * Math.PI) * 0.4 + 0.4;
    const randomVariation = (Math.random() - 0.5) * 0.1;
    
    history.push({
      date: date.toISOString().split('T')[0],
      ndvi: Math.max(0, Math.min(1, seasonalFactor + randomVariation)),
      evi: Math.max(0, Math.min(1, seasonalFactor * 0.9 + randomVariation)),
      ndwi: Math.max(-1, Math.min(1, seasonalFactor * 0.7 + randomVariation - 0.2))
    });
  }
  
  return history;
}

// Districts Data
export const districts: DistrictData[] = [
  {
    id: 'dammam',
    name: 'Dammam',
    coordinates: [
      [26.3, 50.0],
      [26.5, 50.0],
      [26.5, 50.2],
      [26.3, 50.2]
    ],
    totalArea: 285000,
    cultivatedArea: 145000,
    cropBreakdown: { dates: 55, wheat: 25, tomatoes: 15, alfalfa: 5 },
    healthScore: 76,
    alerts: 23
  },
  {
    id: 'alkhobar',
    name: 'Al Khobar',
    coordinates: [
      [26.2, 50.1],
      [26.4, 50.1],
      [26.4, 50.3],
      [26.2, 50.3]
    ],
    totalArea: 195000,
    cultivatedArea: 98000,
    cropBreakdown: { dates: 45, wheat: 30, tomatoes: 20, alfalfa: 5 },
    healthScore: 71,
    alerts: 31
  },
  {
    id: 'hofuf',
    name: 'Al Hofuf',
    coordinates: [
      [25.3, 49.5],
      [25.5, 49.5],
      [25.5, 49.7],
      [25.3, 49.7]
    ],
    totalArea: 420000,
    cultivatedArea: 285000,
    cropBreakdown: { dates: 65, wheat: 20, tomatoes: 10, alfalfa: 5 },
    healthScore: 82,
    alerts: 15
  },
  {
    id: 'qatif',
    name: 'Qatif',
    coordinates: [
      [26.5, 50.0],
      [26.6, 50.0],
      [26.6, 50.1],
      [26.5, 50.1]
    ],
    totalArea: 210000,
    cultivatedArea: 155000,
    cropBreakdown: { dates: 70, wheat: 15, tomatoes: 10, alfalfa: 5 },
    healthScore: 68,
    alerts: 28
  },
  {
    id: 'jubail',
    name: 'Al Jubail',
    coordinates: [
      [26.9, 49.6],
      [27.1, 49.6],
      [27.1, 49.8],
      [26.9, 49.8]
    ],
    totalArea: 178000,
    cultivatedArea: 86000,
    cropBreakdown: { dates: 40, wheat: 35, tomatoes: 15, alfalfa: 10 },
    healthScore: 81,
    alerts: 12
  }
];

// Weather Data
export const weatherData: WeatherData = {
  current: {
    temperature: 34,
    condition: 'Partly Cloudy',
    humidity: 65,
    windSpeed: 12,
    precipitation: 0,
    uvIndex: 8
  },
  forecast: [
    { date: '2025-01-27', high: 36, low: 22, condition: 'Sunny', precipitationChance: 5, humidity: 58 },
    { date: '2025-01-28', high: 35, low: 21, condition: 'Partly Cloudy', precipitationChance: 15, humidity: 62 },
    { date: '2025-01-29', high: 33, low: 20, condition: 'Cloudy', precipitationChance: 45, humidity: 70 },
    { date: '2025-01-30', high: 31, low: 19, condition: 'Light Rain', precipitationChance: 75, humidity: 78 },
    { date: '2025-01-31', high: 32, low: 18, condition: 'Partly Cloudy', precipitationChance: 20, humidity: 68 }
  ]
};

// Vegetation Index Time Series
export const vegetationIndexData: VegetationIndex[] = [
  { date: '2024-11-01', ndvi: 0.35, evi: 0.32, ndwi: -0.15, savi: 0.38 },
  { date: '2024-11-15', ndvi: 0.42, evi: 0.39, ndwi: -0.08, savi: 0.45 },
  { date: '2024-12-01', ndvi: 0.51, evi: 0.48, ndwi: 0.02, savi: 0.54 },
  { date: '2024-12-15', ndvi: 0.58, evi: 0.55, ndwi: 0.08, savi: 0.61 },
  { date: '2025-01-01', ndvi: 0.65, evi: 0.62, ndwi: 0.15, savi: 0.68 },
  { date: '2025-01-15', ndvi: 0.72, evi: 0.69, ndwi: 0.22, savi: 0.75 },
  { date: '2025-01-26', ndvi: 0.78, evi: 0.75, ndwi: 0.28, savi: 0.81 }
];

// Analytics Data
export const analyticsData: AnalyticsData = {
  cropAreaTrends: [
    { year: 2020, dates: 920000, wheat: 480000, tomatoes: 280000, alfalfa: 350000 },
    { year: 2021, dates: 935000, wheat: 495000, tomatoes: 290000, alfalfa: 360000 },
    { year: 2022, dates: 950000, wheat: 510000, tomatoes: 300000, alfalfa: 370000 },
    { year: 2023, dates: 965000, wheat: 525000, tomatoes: 310000, alfalfa: 380000 },
    { year: 2024, dates: 985000, wheat: 520000, tomatoes: 280000, alfalfa: 355000 }
  ],
  yieldPredictions: [
    { month: 'Nov', predicted: 3.2, confidence: [2.8, 3.6] },
    { month: 'Dec', predicted: 3.5, confidence: [3.1, 3.9] },
    { month: 'Jan', predicted: 3.8, confidence: [3.4, 4.2] },
    { month: 'Feb', predicted: 4.1, confidence: [3.7, 4.5] },
    { month: 'Mar', predicted: 4.3, confidence: [3.9, 4.7] },
    { month: 'Apr', predicted: 4.5, actual: 4.2, confidence: [4.1, 4.9] }
  ],
  healthDistribution: [
    { status: 'Healthy', percentage: 68, area: 1931200 },
    { status: 'Moderate Stress', percentage: 24, area: 681600 },
    { status: 'High Stress', percentage: 8, area: 227200 }
  ]
};

// Map Layer Configurations
export const mapLayers = {
  baseLayers: [
    { id: 'osm', name: 'OpenStreetMap', url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', attribution: '© OpenStreetMap contributors' },
    { id: 'satellite', name: 'Satellite', url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attribution: '© Esri' },
    { id: 'terrain', name: 'Terrain', url: 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', attribution: '© OpenTopoMap' }
  ],
  dataLayers: [
    { id: 'ndvi', name: 'NDVI', visible: true, opacity: 0.8 },
    { id: 'crops', name: 'Crop Types', visible: true, opacity: 1 },
    { id: 'moisture', name: 'Soil Moisture', visible: false, opacity: 0.7 },
    { id: 'temperature', name: 'Land Surface Temp', visible: false, opacity: 0.7 },
    { id: 'stress', name: 'Water Stress Index', visible: false, opacity: 0.8 }
  ]
};

// Available Satellite Dates for Eastern Province
export const availableSatelliteDates = [
  { date: '2024-11-01', sourceId: 'sentinel-2', sourceName: 'Sentinel-2', cloudCover: 5, available: true },
  { date: '2024-11-06', sourceId: 'sentinel-2', sourceName: 'Sentinel-2', cloudCover: 12, available: true },
  { date: '2024-11-11', sourceId: 'sentinel-2', sourceName: 'Sentinel-2', cloudCover: 3, available: true },
  { date: '2024-11-16', sourceId: 'sentinel-2', sourceName: 'Sentinel-2', cloudCover: 25, available: false },
  { date: '2024-11-21', sourceId: 'sentinel-2', sourceName: 'Sentinel-2', cloudCover: 8, available: true },
  { date: '2024-11-26', sourceId: 'sentinel-2', sourceName: 'Sentinel-2', cloudCover: 2, available: true },
  { date: '2024-12-01', sourceId: 'landsat', sourceName: 'Landsat 8/9', cloudCover: 10, available: true },
  { date: '2024-12-06', sourceId: 'sentinel-2', sourceName: 'Sentinel-2', cloudCover: 15, available: true },
  { date: '2024-12-11', sourceId: 'sentinel-2', sourceName: 'Sentinel-2', cloudCover: 4, available: true },
  { date: '2024-12-16', sourceId: 'modis', sourceName: 'MODIS', cloudCover: 8, available: true },
  { date: '2024-12-21', sourceId: 'sentinel-2', sourceName: 'Sentinel-2', cloudCover: 20, available: true },
  { date: '2024-12-26', sourceId: 'sentinel-2', sourceName: 'Sentinel-2', cloudCover: 6, available: true },
  { date: '2024-12-31', sourceId: 'landsat', sourceName: 'Landsat 8/9', cloudCover: 12, available: true },
  { date: '2025-01-05', sourceId: 'sentinel-2', sourceName: 'Sentinel-2', cloudCover: 7, available: true },
  { date: '2025-01-10', sourceId: 'modis', sourceName: 'MODIS', cloudCover: 5, available: true },
  { date: '2025-01-15', sourceId: 'sentinel-2', sourceName: 'Sentinel-2', cloudCover: 3, available: true },
  { date: '2025-01-20', sourceId: 'sentinel-2', sourceName: 'Sentinel-2', cloudCover: 18, available: true },
  { date: '2025-01-26', sourceId: 'sentinel-2', sourceName: 'Sentinel-2', cloudCover: 4, available: true }
];

// Pre-calculated index results for demonstration
export const indexResults = {
  '2025-01-26': {
    ndvi: { min: -0.15, max: 0.92, mean: 0.58, stdDev: 0.18, indexId: 'ndvi', indexName: 'NDVI' },
    evi: { min: -0.22, max: 0.88, mean: 0.52, stdDev: 0.16, indexId: 'evi', indexName: 'EVI' },
    ndwi: { min: -0.45, max: 0.65, mean: 0.12, stdDev: 0.22, indexId: 'ndwi', indexName: 'NDWI' },
    savi: { min: -0.18, max: 0.85, mean: 0.54, stdDev: 0.17, indexId: 'savi', indexName: 'SAVI' },
    msi: { min: 0.65, max: 2.45, mean: 1.32, stdDev: 0.35, indexId: 'msi', indexName: 'MSI' },
    nbr: { min: -0.35, max: 0.78, mean: 0.42, stdDev: 0.19, indexId: 'nbr', indexName: 'NBR' },
    lai: { min: 0.1, max: 5.8, mean: 3.2, stdDev: 1.1, indexId: 'lai', indexName: 'LAI' },
    gndvi: { min: -0.12, max: 0.85, mean: 0.51, stdDev: 0.17, indexId: 'gndvi', indexName: 'GNDVI' }
  },
  '2025-01-15': {
    ndvi: { min: -0.12, max: 0.88, mean: 0.55, stdDev: 0.17, indexId: 'ndvi', indexName: 'NDVI' },
    evi: { min: -0.20, max: 0.85, mean: 0.49, stdDev: 0.15, indexId: 'evi', indexName: 'EVI' },
    ndwi: { min: -0.42, max: 0.62, mean: 0.10, stdDev: 0.21, indexId: 'ndwi', indexName: 'NDWI' },
    savi: { min: -0.15, max: 0.82, mean: 0.51, stdDev: 0.16, indexId: 'savi', indexName: 'SAVI' },
    msi: { min: 0.70, max: 2.55, mean: 1.38, stdDev: 0.37, indexId: 'msi', indexName: 'MSI' },
    nbr: { min: -0.32, max: 0.75, mean: 0.40, stdDev: 0.18, indexId: 'nbr', indexName: 'NBR' },
    lai: { min: 0.1, max: 5.5, mean: 3.0, stdDev: 1.0, indexId: 'lai', indexName: 'LAI' },
    gndvi: { min: -0.10, max: 0.82, mean: 0.48, stdDev: 0.16, indexId: 'gndvi', indexName: 'GNDVI' }
  }
};

// Histogram data for NDVI visualization
export function generateHistogramData(mean: number, stdDev: number): { value: number; count: number }[] {
  const histogram: { value: number; count: number }[] = [];
  for (let i = -2; i <= 10; i++) {
    const value = i * 0.1;
    const zScore = (value - mean) / stdDev;
    const count = Math.max(0, Math.exp(-0.5 * zScore * zScore) * 1000 + Math.random() * 100);
    histogram.push({ value, count: Math.round(count) });
  }
  return histogram;
}

// Eastern Province bounds for satellite imagery
export const easternProvinceBounds: [[number, number], [number, number], [number, number], [number, number]] = [
  [25.5, 49.0],  // Southwest
  [25.5, 51.0],  // Southeast
  [27.5, 51.0],  // Northeast
  [27.5, 49.0]   // Northwest
];

// Regions of interest for detailed analysis
export const regionsOfInterest = [
  {
    id: 'alahsa-oasis',
    name: 'Al-Ahsa Oasis',
    bounds: [[25.3, 49.5], [25.3, 49.7], [25.5, 49.7], [25.5, 49.5]] as [[number, number], [number, number], [number, number], [number, number]],
    area: 850000
  },
  {
    id: 'coastal-farms',
    name: 'Coastal Farming Region',
    bounds: [[26.3, 50.0], [26.3, 50.3], [26.6, 50.3], [26.6, 50.0]] as [[number, number], [number, number], [number, number], [number, number]],
    area: 420000
  },
  {
    id: 'industrial-zone',
    name: 'Jubail Agricultural Zone',
    bounds: [[26.9, 49.6], [26.9, 49.8], [27.1, 49.8], [27.1, 49.6]] as [[number, number], [number, number], [number, number], [number, number]],
    area: 180000
  }
];

// Temporal comparison data
export const temporalComparisons = [
  {
    date1: '2025-01-15',
    date2: '2025-01-26',
    indexId: 'ndvi',
    changeMap: [
      { category: 'Significant Decline (>20%)', value: -20, area: 85000, color: '#dc2626' },
      { category: 'Moderate Decline (10-20%)', value: -15, area: 120000, color: '#f97316' },
      { category: 'Slight Decline (5-10%)', value: -7, area: 180000, color: '#fbbf24' },
      { category: 'Stable (±5%)', value: 0, area: 1850000, color: '#d1d5db' },
      { category: 'Slight Increase (5-10%)', value: 7, area: 320000, color: '#86efac' },
      { category: 'Moderate Increase (10-20%)', value: 15, area: 150000, color: '#22c55e' },
      { category: 'Significant Increase (>20%)', value: 25, area: 75000, color: '#15803d' }
    ]
  }
];
