/**
 * useWeather Hook
 *
 * Custom hook for fetching weather data
 */

import { useQuery } from '@tanstack/react-query';
import { getCurrentWeather, getWeatherForecast, getFieldWeather } from '@/services/weather';
import type { WeatherData, DailyForecast } from '@/types';

/**
 * Query keys for weather-related queries
 */
export const weatherKeys = {
  all: ['weather'] as const,
  current: (lat: number, lng: number) => [...weatherKeys.all, 'current', lat, lng] as const,
  forecast: (lat: number, lng: number, days: number) =>
    [...weatherKeys.all, 'forecast', lat, lng, days] as const,
  field: (fieldId: string) => [...weatherKeys.all, 'field', fieldId] as const,
};

/**
 * Hook to fetch current weather for a location
 */
export function useCurrentWeather(
  latitude: number | null,
  longitude: number | null,
  enabled = true
) {
  return useQuery({
    queryKey: weatherKeys.current(latitude || 0, longitude || 0),
    queryFn: () => getCurrentWeather(latitude!, longitude!),
    enabled: enabled && latitude !== null && longitude !== null,
    select: (data) => ({
      ...data.weather,
      observationTime: new Date(data.weather.observation_time),
    }),
    staleTime: 15 * 60 * 1000, // 15 minutes
    refetchInterval: 15 * 60 * 1000, // Refetch every 15 minutes
  });
}

/**
 * Hook to fetch weather forecast
 */
export function useWeatherForecast(
  latitude: number | null,
  longitude: number | null,
  days: number = 5,
  enabled = true
) {
  return useQuery({
    queryKey: weatherKeys.forecast(latitude || 0, longitude || 0, days),
    queryFn: () => getWeatherForecast(latitude!, longitude!, days),
    enabled: enabled && latitude !== null && longitude !== null,
    select: (data) => ({
      daily: data.daily.map((d) => ({
        ...d,
        date: new Date(d.date),
      })),
      hourly: data.hourly?.map((h) => ({
        ...h,
        datetime: new Date(h.datetime),
      })),
      generatedAt: new Date(data.generated_at),
    }),
    staleTime: 6 * 60 * 60 * 1000, // 6 hours
    refetchInterval: 6 * 60 * 60 * 1000, // Refetch every 6 hours
  });
}

/**
 * Hook to fetch both current weather and forecast
 */
export function useWeather(latitude: number | null, longitude: number | null, enabled = true) {
  const current = useCurrentWeather(latitude, longitude, enabled);
  const forecast = useWeatherForecast(latitude, longitude, 5, enabled);

  return {
    current: current.data,
    forecast: forecast.data?.daily,
    isLoading: current.isLoading || forecast.isLoading,
    error: current.error || forecast.error,
    refetch: () => {
      current.refetch();
      forecast.refetch();
    },
  };
}

/**
 * Hook to fetch weather for a field
 */
export function useFieldWeather(fieldLatitude: number | null, fieldLongitude: number | null) {
  return useQuery({
    queryKey: weatherKeys.current(fieldLatitude || 0, fieldLongitude || 0),
    queryFn: async () => {
      if (!fieldLatitude || !fieldLongitude) {
        throw new Error('Field coordinates required');
      }
      return getFieldWeather(fieldLatitude, fieldLongitude);
    },
    enabled: fieldLatitude !== null && fieldLongitude !== null,
    staleTime: 15 * 60 * 1000, // 15 minutes
    refetchInterval: 15 * 60 * 1000,
  });
}

/**
 * Hook to get weather summary for dashboard
 */
export function useWeatherSummary(latitude: number, longitude: number) {
  const current = useCurrentWeather(latitude, longitude);
  const forecast = useWeatherForecast(latitude, longitude, 1);

  const today = forecast.data?.daily?.[0];

  return {
    current: current.data,
    todayHigh: today?.temp_max,
    todayLow: today?.temp_min,
    todayCondition: today?.condition,
    precipitationProbability: today?.precipitation_probability,
    isLoading: current.isLoading || forecast.isLoading,
    error: current.error || forecast.error,
  };
}
