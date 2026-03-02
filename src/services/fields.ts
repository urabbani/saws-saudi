/**
 * SAWS Fields API Service
 *
 * API calls for agricultural field management
 */

import { apiClient, PaginatedResponse, PaginationParams } from './api';
import type { FieldData } from '@/types';

/**
 * Field geometry type (GeoJSON)
 */
export interface FieldGeometry {
  type: 'Polygon';
  coordinates: number[][][];
}

/**
 * Field creation data
 */
export interface FieldCreate {
  name: string;
  description?: string;
  district_id: string;
  geometry: FieldGeometry;
  area_hectares: number;
  crop_type: string;
  variety?: string;
  owner_id: string;
  owner_name: string;
}

/**
 * Field update data
 */
export interface FieldUpdate {
  name?: string;
  description?: string;
  crop_type?: string;
  variety?: string;
  status?: string;
}

/**
 * Field detail with latest satellite data
 */
export interface FieldDetail extends FieldData {
  latest_ndvi?: number;
  latest_ndvi_date?: string;
  health_status?: 'excellent' | 'good' | 'moderate' | 'poor';
}

/**
 * List all fields with optional filters
 */
export async function listFields(
  params: PaginationParams & {
    district?: string;
    crop_type?: string;
  } = {}
): Promise<PaginatedResponse<FieldData>> {
  return apiClient.get('/fields', { params });
}

/**
 * Get field details by ID
 */
export async function getField(fieldId: string): Promise<FieldDetail> {
  return apiClient.get(`/fields/${fieldId}`);
}

/**
 * Create a new field
 */
export async function createField(data: FieldCreate): Promise<FieldDetail> {
  return apiClient.post('/fields', data);
}

/**
 * Update an existing field
 */
export async function updateField(fieldId: string, data: FieldUpdate): Promise<FieldDetail> {
  return apiClient.put(`/fields/${fieldId}`, data);
}

/**
 * Delete a field
 */
export async function deleteField(fieldId: string): Promise<void> {
  return apiClient.delete(`/fields/${fieldId}`);
}

/**
 * Get field statistics
 */
export interface FieldStats {
  total_fields: number;
  total_area_hectares: number;
  fields_by_crop_type: Record<string, number>;
  fields_by_status: Record<string, number>;
  fields_by_district: Record<string, number>;
  health_distribution: Record<string, number>;
}

export async function getFieldStats(): Promise<FieldStats> {
  return apiClient.get('/fields/stats');
}

/**
 * Convert FieldDetail to frontend FieldData format
 */
export function toFieldData(detail: FieldDetail): FieldData {
  return {
    id: detail.id,
    name: detail.name,
    district: detail.district_id,
    crop: detail.crop_type as any,
    area: detail.area_hectares,
    coordinates: detail.geometry?.coordinates?.[0] || [],
    centroid: {
      lat: detail.centroid_latitude,
      lng: detail.centroid_longitude,
    },
    ndvi: detail.latest_ndvi,
    soilMoisture: detail.soil_moisture,
    status: detail.status as any,
    variety: detail.variety,
    owner: {
      id: detail.owner_id,
      name: detail.owner_name,
    },
    healthStatus: detail.health_status || 'moderate',
    alerts: detail.alerts || 0,
    lastUpdated: detail.updated_at || new Date().toISOString(),
  };
}
