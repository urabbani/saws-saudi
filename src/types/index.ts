// Dashboard Types

export interface KPIData {
  id: string;
  title: string;
  value: string;
  unit: string;
  trend: number;
  trendLabel: string;
  icon: string;
  sparklineData: number[];
  status: 'positive' | 'negative' | 'neutral' | 'warning';
}

export interface CropType {
  id: string;
  name: string;
  color: string;
  area: number;
  healthScore: number;
  trend: number;
}

export interface SatelliteSource {
  id: string;
  name: string;
  resolution: string;
  revisitTime: string;
  status: 'active' | 'delayed' | 'offline';
  lastUpdate: string;
  description: string;
  useCases: string[];
  icon: string;
}

export interface Alert {
  id: string;
  user_id: string;
  field_id?: string;
  severity: 'critical' | 'warning' | 'advisory' | 'info';
  alert_type: 'drought' | 'low_ndvi' | 'soil_moisture' | 'extreme_temperature' | 'pest_detection' | 'irrigation_needed' | 'frost_warning' | 'harvest_ready';
  title: string;
  message: string;
  district?: string;
  priority: number;
  data?: Record<string, unknown>;
  is_read: boolean;
  read_at?: string;
  email_sent: boolean;
  sms_sent: boolean;
  whatsapp_sent: boolean;
  created_at: string;
  expires_at?: string;
}

export interface FieldData {
  id: string;
  name: string;
  coordinates: [number, number][];
  center: [number, number];
  area: number;
  cropType: string;
  ndvi: number;
  healthStatus: 'healthy' | 'moderate' | 'stressed';
  plantingDate: string;
  expectedHarvest: string;
  yieldEstimate: number;
  waterStressIndex: number;
  soilMoisture: number;
  history: NDVIPoint[];
}

export interface NDVIPoint {
  date: string;
  ndvi: number;
  evi: number;
  ndwi: number;
}

export interface VegetationIndex {
  date: string;
  ndvi: number;
  evi: number;
  ndwi: number;
  savi: number;
}

export interface DistrictData {
  id: string;
  name: string;
  coordinates: [number, number][];
  totalArea: number;
  cultivatedArea: number;
  cropBreakdown: Record<string, number>;
  healthScore: number;
  alerts: number;
}

export interface WeatherData {
  current: {
    temperature: number;
    condition: string;
    humidity: number;
    windSpeed: number;
    precipitation: number;
    uvIndex: number;
  };
  forecast: DailyForecast[];
}

export interface DailyForecast {
  date: string;
  high: number;
  low: number;
  condition: string;
  precipitationChance: number;
  humidity: number;
}

export interface MapLayer {
  id: string;
  name: string;
  type: 'raster' | 'vector' | 'overlay';
  visible: boolean;
  opacity: number;
  legend?: LegendItem[];
  url?: string;
}

export interface LegendItem {
  color: string;
  label: string;
  value?: number;
}

export interface AnalyticsData {
  cropAreaTrends: {
    year: number;
    wheat: number;
    rice: number;
    cotton: number;
    sugarcane: number;
  }[];
  yieldPredictions: {
    month: string;
    predicted: number;
    actual?: number;
    confidence: [number, number];
  }[];
  healthDistribution: {
    status: string;
    percentage: number;
    area: number;
  }[];
}

export interface TimeSeriesData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    color: string;
    fill?: boolean;
  }[];
}

// Satellite Imagery Types
export interface SatelliteImage {
  id: string;
  sourceId: string;
  sourceName: string;
  date: string;
  acquisitionTime: string;
  cloudCover: number;
  bounds: [[number, number], [number, number], [number, number], [number, number]];
  resolution: number;
  url?: string;
  metadata: SatelliteMetadata;
}

export interface SatelliteMetadata {
  product: string;
  processingLevel: string;
  bands: SpectralBand[];
  sunElevation: number;
  sunAzimuth: number;
  sensor: string;
}

export interface SpectralBand {
  id: string;
  name: string;
  wavelength: string;
  resolution: number;
  description: string;
}

export interface VegetationIndexConfig {
  id: string;
  name: string;
  formula: string;
  description: string;
  range: [number, number];
  colorScale: ColorScaleStop[];
  unit: string;
}

export interface ColorScaleStop {
  value: number;
  color: string;
  label: string;
}

export interface IndexCalculationResult {
  indexId: string;
  indexName: string;
  date: string;
  min: number;
  max: number;
  mean: number;
  stdDev: number;
  histogram: HistogramData[];
  imageUrl?: string;
}

export interface HistogramData {
  value: number;
  count: number;
}

export interface TemporalComparison {
  date1: string;
  date2: string;
  indexId: string;
  differenceUrl?: string;
  changeMap: ChangeMapData[];
}

export interface ChangeMapData {
  category: string;
  value: number;
  area: number;
  color: string;
}

export interface AvailableSatelliteDate {
  date: string;
  sourceId: string;
  sourceName: string;
  cloudCover: number;
  available: boolean;
}

export interface RegionOfInterest {
  id: string;
  name: string;
  bounds: [[number, number], [number, number], [number, number], [number, number]];
  area: number;
}

export interface BandCombination {
  id: string;
  name: string;
  redBand: string;
  greenBand: string;
  blueBand: string;
  description: string;
}
