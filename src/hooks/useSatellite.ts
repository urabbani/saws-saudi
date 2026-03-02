/**
 * useSatellite Hook
 *
 * Custom hook for fetching satellite imagery and vegetation indices
 */

import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
  listSatelliteSources,
  getVegetationIndices,
  getNDVITimeSeries,
  getLatestNDVI,
  toChartData,
  type VegetationIndexType,
  type SatelliteImage,
  type VegetationIndexSeries,
} from '@/services/satellite';

/**
 * Query keys for satellite-related queries
 */
export const satelliteKeys = {
  all: ['satellite'] as const,
  sources: () => [...satelliteKeys.all, 'sources'] as const,
  images: () => [...satelliteKeys.all, 'images'] as const,
  indices: (fieldId: string, indexType: VegetationIndexType) =>
    [...satelliteKeys.all, 'indices', fieldId, indexType] as const,
  latest: (fieldId: string) => [...satelliteKeys.all, 'latest', fieldId] as const,
};

/**
 * Hook to fetch available satellite sources
 */
export function useSatelliteSources() {
  return useQuery({
    queryKey: satelliteKeys.sources(),
    queryFn: listSatelliteSources,
    select: (data) => data.items,
    staleTime: 60 * 60 * 1000, // 1 hour - sources don't change often
  });
}

/**
 * Hook to fetch satellite images
 */
export function useSatelliteImages(params: {
  source?: string;
  start_date?: string;
  end_date?: string;
  skip?: number;
  limit?: number;
}) {
  return useQuery({
    queryKey: [...satelliteKeys.images(), params],
    queryFn: () =>
      import('./services/satellite').then((m) => m.listSatelliteImages(params)),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to fetch vegetation indices for a field
 */
export function useVegetationIndices(
  fieldId: string | null,
  indexType: VegetationIndexType = 'ndvi',
  startDate?: string,
  endDate?: string
) {
  return useQuery({
    queryKey: satelliteKeys.indices(fieldId || '', indexType),
    queryFn: () => getVegetationIndices(fieldId!, indexType, startDate, endDate),
    enabled: !!fieldId,
    select: toChartData,
    staleTime: 24 * 60 * 60 * 1000, // 24 hours - satellite data doesn't change rapidly
  });
}

/**
 * Hook to fetch NDVI time series for a field
 */
export function useNDVI(fieldId: string | null, startDate?: string, endDate?: string) {
  return useVegetationIndices(fieldId, 'ndvi', startDate, endDate);
}

/**
 * Hook to fetch latest NDVI value for a field
 */
export function useLatestNDVI(fieldId: string | null) {
  return useQuery({
    queryKey: satelliteKeys.latest(fieldId || ''),
    queryFn: () => getLatestNDVI(fieldId!),
    enabled: !!fieldId,
    staleTime: 24 * 60 * 60 * 1000, // 24 hours
  });
}

/**
 * Hook to fetch EVI time series for a field
 */
export function useEVI(fieldId: string | null, startDate?: string, endDate?: string) {
  return useVegetationIndices(fieldId, 'evi', startDate, endDate);
}

/**
 * Hook to fetch NDMI (moisture index) time series for a field
 */
export function useNDMI(fieldId: string | null, startDate?: string, endDate?: string) {
  return useVegetationIndices(fieldId, 'ndmi', startDate, endDate);
}

/**
 * Hook to get crop health status based on NDVI
 */
export function useCropHealth(fieldId: string | null) {
  const { data: latestNDVI } = useLatestNDVI(fieldId);

  return useQuery({
    queryKey: ['cropHealth', fieldId, latestNDVI?.value],
    queryFn: () => {
      const ndvi = latestNDVI?.value;
      if (ndvi === undefined || ndvi === null) {
        return { status: 'unknown' as const, ndvi: null };
      }

      let status: 'excellent' | 'good' | 'moderate' | 'poor';
      if (ndvi > 0.6) {
        status = 'excellent';
      } else if (ndvi > 0.4) {
        status = 'good';
      } else if (ndvi > 0.2) {
        status = 'moderate';
      } else {
        status = 'poor';
      }

      return { status, ndvi, date: latestNDVI?.date };
    },
    enabled: !!fieldId && latestNDVI !== undefined,
    staleTime: 24 * 60 * 60 * 1000,
  });
}

/**
 * Hook to compare multiple vegetation indices
 */
export function useVegetationComparison(fieldId: string | null, startDate?: string, endDate?: string) {
  const queryClient = useQueryClient();

  const ndvi = useNDVI(fieldId, startDate, endDate);
  const evi = useEVI(fieldId, startDate, endDate);
  const ndmi = useNDMI(fieldId, startDate, endDate);

  return {
    ndvi: ndvi.data,
    evi: evi.data,
    ndmi: ndmi.data,
    isLoading: ndvi.isLoading || evi.isLoading || ndmi.isLoading,
    error: ndvi.error || evi.error || ndmi.error,
    refetch: () => {
      queryClient.invalidateQueries({ queryKey: satelliteKeys.indices(fieldId || '', 'ndvi') });
      queryClient.invalidateQueries({ queryKey: satelliteKeys.indices(fieldId || '', 'evi') });
      queryClient.invalidateQueries({ queryKey: satelliteKeys.indices(fieldId || '', 'ndmi') });
    },
  };
}

/**
 * Hook to get historical NDVI trend (last 12 months)
 */
export function useNDVITrend(fieldId: string | null) {
  const endDate = new Date().toISOString().split('T')[0];
  const startDate = new Date(Date.now() - 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

  return useNDVI(fieldId, startDate, endDate);
}

/**
 * Hook to get seasonal NDVI data
 */
export function useSeasonalNDVI(fieldId: string | null, months: number = 3) {
  const endDate = new Date().toISOString().split('T')[0];
  const startDate = new Date(Date.now() - months * 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

  return useNDVI(fieldId, startDate, endDate);
}
