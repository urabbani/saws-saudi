/**
 * useAnalytics Hook
 *
 * Custom hook for fetching analytics data
 */

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/services/api';

/**
 * Query keys for analytics-related queries
 */
export const analyticsKeys = {
  all: ['analytics'] as const,
  trends: (params: Record<string, unknown>) => [...analyticsKeys.all, 'trends', params] as const,
  predictions: (fieldId: string) => [...analyticsKeys.all, 'predictions', fieldId] as const,
  droughtStatus: (location: { lat: number; lng: number }) =>
    [...analyticsKeys.all, 'droughtStatus', location] as const,
  droughtForecast: (location: { lat: number; lng: number }) =>
    [...analyticsKeys.all, 'droughtForecast', location] as const,
  healthDistribution: (params: Record<string, unknown>) =>
    [...analyticsKeys.all, 'healthDistribution', params] as const,
};

/**
 * Crop trends data
 */
export interface CropTrendsData {
  field_id?: string;
  crop_type?: string;
  start_date?: string;
  end_date?: string;
  ndvi_trend: Array<{ date: string; value: number }>;
  evi_trend?: Array<{ date: string; value: number }>;
  statistics?: {
    min: number;
    max: number;
    mean: number;
    trend_slope: number;
  };
  health_status?: string;
}

/**
 * Yield prediction data
 */
export interface YieldPredictionData {
  field_id: string;
  prediction: {
    predicted_yield: number;
    confidence_interval: [number, number];
    confidence_level: number;
    prediction_date: string;
    expected_harvest_date?: string;
    model_version: string;
    factors?: Record<string, unknown>;
  };
}

/**
 * Drought status data
 */
export interface DroughtStatusData {
  latitude: number;
  longitude: number;
  spei_value: number;
  spei_scale: number;
  status: 'extreme' | 'severe' | 'moderate' | 'abnormally_dry' | 'normal' | 'wet';
  status_changed_at?: string;
  trend?: 'improving' | 'worsening' | 'stable';
  contributing_factors?: Record<string, unknown>;
}

/**
 * Drought forecast data
 */
export interface DroughtForecastData {
  latitude: number;
  longitude: number;
  forecast_days: number;
  generated_at: string;
  model_version: string;
  forecast: Array<{
    date: string;
    spei_predicted: number;
    spei_lower_bound?: number;
    spei_upper_bound?: number;
    status: string;
  }>;
}

/**
 * Hook to fetch crop trends
 */
export function useCropTrends(params: {
  fieldId?: string;
  cropType?: string;
  startDate?: string;
  endDate?: string;
}) {
  return useQuery({
    queryKey: analyticsKeys.trends(params),
    queryFn: () =>
      apiClient.get<CropTrendsData>('/analytics/trends', {
        params: {
          field_id: params.fieldId,
          crop_type: params.cropType,
          start_date: params.startDate,
          end_date: params.endDate,
        },
      }),
    enabled: !!(params.fieldId || params.cropType),
    staleTime: 24 * 60 * 60 * 1000, // 24 hours
  });
}

/**
 * Hook to fetch yield prediction for a field
 */
export function useYieldPrediction(fieldId: string | null) {
  return useQuery({
    queryKey: analyticsKeys.predictions(fieldId || ''),
    queryFn: () => apiClient.get<YieldPredictionData>(`/analytics/predictions/yield?field_id=${fieldId}`),
    enabled: !!fieldId,
    staleTime: 7 * 24 * 60 * 60 * 1000, // 7 days - predictions don't change rapidly
  });
}

/**
 * Hook to fetch drought status for a location
 */
export function useDroughtStatus(latitude: number | null, longitude: number | null) {
  return useQuery({
    queryKey: analyticsKeys.droughtStatus({ lat: latitude || 0, lng: longitude || 0 }),
    queryFn: () =>
      apiClient.get<DroughtStatusData>('/analytics/drought/status', {
        params: { latitude, longitude, spei_scale: 3 },
      }),
    enabled: latitude !== null && longitude !== null,
    staleTime: 12 * 60 * 60 * 1000, // 12 hours
    refetchInterval: 12 * 60 * 60 * 1000,
  });
}

/**
 * Hook to fetch drought forecast
 */
export function useDroughtForecast(
  latitude: number | null,
  longitude: number | null,
  forecastDays: number = 30
) {
  return useQuery({
    queryKey: [...analyticsKeys.droughtForecast({ lat: latitude || 0, lng: longitude || 0 }), forecastDays],
    queryFn: () =>
      apiClient.get<DroughtForecastData>('/analytics/drought/forecast', {
        params: { latitude, longitude, forecast_days: forecastDays },
      }),
    enabled: latitude !== null && longitude !== null,
    staleTime: 24 * 60 * 60 * 1000, // 24 hours
  });
}

/**
 * Hook to fetch crop health distribution
 */
export function useCropHealthDistribution(params: { district?: string; cropType?: string } = {}) {
  return useQuery({
    queryKey: analyticsKeys.healthDistribution(params),
    queryFn: () =>
      apiClient.get<Record<string, number>>('/analytics/health/distribution', {
        params: { district: params.district, crop_type: params.cropType },
      }),
    staleTime: 24 * 60 * 60 * 1000, // 24 hours
  });
}
