/**
 * SAWS Satellite API Service
 *
 * API calls for satellite imagery and vegetation indices
 */

import { apiClient, PaginatedResponse, PaginationParams } from './api';

/**
 * Satellite source types
 */
export type SatelliteSource = 'modis' | 'landsat' | 'sentinel1' | 'sentinel2' | 'planet';

/**
 * Vegetation index types
 */
export type VegetationIndexType = 'ndvi' | 'evi' | 'savi' | 'msavi' | 'ndmi' | 'lst';

/**
 * Satellite source information
 */
export interface SatelliteSourceInfo {
  source: SatelliteSource;
  name: string;
  description: string;
  resolution: string;
  revisit_time: string;
  coverage: string;
  cost: string;
  available: boolean;
}

/**
 * Satellite image metadata
 */
export interface SatelliteImage {
  id: string;
  field_id: string;
  source: SatelliteSource;
  image_id: string;
  collection_id: string;
  acquisition_date: string;
  image_date: string;
  cloud_cover: number;
  ndvi?: number;
  evi?: number;
  lst?: number;
  quality_score: number;
}

/**
 * NDVI value at a point in time
 */
export interface NDVIPoint {
  date: string;
  value: number;
  source?: SatelliteSource;
  cloud_cover?: number;
}

/**
 * Vegetation index time series
 */
export interface VegetationIndexSeries {
  field_id: string;
  index_type: VegetationIndexType;
  start_date?: string;
  end_date?: string;
  data: NDVIPoint[];
  statistics?: {
    min: number;
    max: number;
    mean: number;
    std: number;
  };
}

/**
 * List available satellite sources
 */
export async function listSatelliteSources(): Promise<{ items: SatelliteSourceInfo[] }> {
  return apiClient.get('/satellite/sources');
}

/**
 * List satellite images
 */
export async function listSatelliteImages(
  params: PaginationParams & {
    source?: SatelliteSource;
    start_date?: string;
    end_date?: string;
  } = {}
): Promise<PaginatedResponse<SatelliteImage>> {
  return apiClient.get('/satellite/images', { params });
}

/**
 * Get vegetation indices for a field
 */
export async function getVegetationIndices(
  fieldId: string,
  indexType: VegetationIndexType = 'ndvi',
  startDate?: string,
  endDate?: string
): Promise<VegetationIndexSeries> {
  const params: Record<string, string> = { index_type: indexType };
  if (startDate) params.start_date = startDate;
  if (endDate) params.end_date = endDate;

  return apiClient.get(`/satellite/indices/${fieldId}`, { params });
}

/**
 * Get NDVI time series for a field
 */
export async function getNDVITimeSeries(
  fieldId: string,
  startDate?: string,
  endDate?: string
): Promise<VegetationIndexSeries> {
  return getVegetationIndices(fieldId, 'ndvi', startDate, endDate);
}

/**
 * Get latest NDVI value for a field
 */
export async function getLatestNDVI(fieldId: string): Promise<NDVIPoint | null> {
  const series = await getNDVITimeSeries(fieldId);
  if (series.data.length === 0) return null;
  // Return most recent data point
  return series.data.sort(
    (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
  )[0];
}

/**
 * Convert API NDVI point to frontend format
 */
export function toNDVIPoint(point: NDVIPoint): { date: Date; value: number } {
  return {
    date: new Date(point.date),
    value: point.value,
  };
}

/**
 * Convert time series to chart format
 */
export function toChartData(series: VegetationIndexSeries): Array<{ date: Date; value: number }> {
  return series.data.map(toNDVIPoint);
}
