/**
 * SAWS Weather API Service
 *
 * API calls for weather data
 */

import { apiClient } from './api';
import type { WeatherData, DailyForecast } from '@/types';

/**
 * Current weather conditions
 */
export interface CurrentWeather {
  temperature: number;
  feels_like?: number;
  humidity: number;
  dew_point?: number;
  wind_speed: number;
  wind_direction: number;
  wind_gust?: number;
  pressure?: number;
  visibility?: number;
  cloud_cover?: number;
  uv_index?: number;
  precipitation?: number;
  condition: string;
  observation_time: string;
  district?: string;
  station_id?: string;
}

/**
 * Current weather response
 */
export interface CurrentWeatherResponse {
  latitude: number;
  longitude: number;
  weather: CurrentWeather;
}

/**
 * Hourly forecast
 */
export interface HourlyForecast {
  datetime: string;
  temperature: number;
  feels_like?: number;
  humidity: number;
  wind_speed: number;
  wind_direction: number;
  precipitation?: number;
  precipitation_probability?: number;
  cloud_cover?: number;
  uv_index?: number;
  condition: string;
}

/**
 * Weather forecast response
 */
export interface WeatherForecastResponse {
  latitude: number;
  longitude: number;
  district?: string;
  generated_at: string;
  daily: DailyForecastData[];
  hourly?: HourlyForecast[];
}

/**
 * Daily forecast (API format)
 */
export interface DailyForecastData {
  date: string;
  temp_min: number;
  temp_max: number;
  temp_avg?: number;
  precipitation_total?: number;
  precipitation_probability?: number;
  condition: string;
  description?: string;
  wind_speed_avg?: number;
  wind_gust_max?: number;
  humidity_avg?: number;
  uv_index_max?: number;
}

/**
 * Historical weather observation
 */
export interface HistoricalWeatherData {
  observation_time: string;
  temperature?: number;
  humidity?: number;
  wind_speed?: number;
  wind_direction?: number;
  precipitation?: number;
  pressure?: number;
  cloud_cover?: number;
  uv_index?: number;
  soil_moisture?: number;
  soil_temperature?: number;
}

/**
 * Historical weather response
 */
export interface HistoricalWeatherResponse {
  latitude: number;
  longitude: number;
  start_date: string;
  end_date: string;
  data: HistoricalWeatherData[];
}

/**
 * Get current weather for a location
 */
export async function getCurrentWeather(
  latitude: number,
  longitude: number
): Promise<CurrentWeatherResponse> {
  return apiClient.get('/weather/current', {
    params: { latitude, longitude },
  });
}

/**
 * Get weather forecast for a location
 */
export async function getWeatherForecast(
  latitude: number,
  longitude: number,
  days: number = 5
): Promise<WeatherForecastResponse> {
  return apiClient.get('/weather/forecast', {
    params: { latitude, longitude, days },
  });
}

/**
 * Get historical weather data
 */
export async function getHistoricalWeather(
  latitude: number,
  longitude: number,
  startDate: string,
  endDate: string
): Promise<HistoricalWeatherResponse> {
  return apiClient.get('/weather/history', {
    params: {
      latitude,
      longitude,
      start_date: startDate,
      end_date: endDate,
    },
  });
}

/**
 * Convert API current weather to frontend format
 */
export function toCurrentWeather(response: CurrentWeatherResponse): WeatherData {
  const w = response.weather;
  return {
    temperature: w.temperature,
    humidity: w.humidity,
    windSpeed: w.wind_speed,
    windDirection: w.wind_direction,
    precipitation: w.precipitation || 0,
    condition: w.condition,
    cloudCover: w.cloud_cover,
    uvIndex: w.uv_index,
    feelsLike: w.feels_like,
    pressure: w.pressure,
    visibility: w.visibility,
    observationTime: new Date(w.observation_time),
  };
}

/**
 * Convert API daily forecast to frontend format
 */
export function toDailyForecast(data: DailyForecastData): DailyForecast {
  return {
    date: new Date(data.date),
    tempMin: data.temp_min,
    tempMax: data.temp_max,
    tempAvg: data.temp_avg,
    condition: data.condition,
    description: data.description,
    precipitation: data.precipitation_total,
    precipitationProbability: data.precipitation_probability,
    windSpeed: data.wind_speed_avg,
    humidity: data.humidity_avg,
    uvIndex: data.uv_index_max,
  };
}

/**
 * Get weather for a field (uses field centroid)
 */
export async function getFieldWeather(
  fieldLatitude: number,
  fieldLongitude: number
): Promise<{
  current: WeatherData;
  forecast: DailyForecast[];
}> {
  const [currentResponse, forecastResponse] = await Promise.all([
    getCurrentWeather(fieldLatitude, fieldLongitude),
    getWeatherForecast(fieldLatitude, fieldLongitude, 5),
  ]);

  return {
    current: toCurrentWeather(currentResponse),
    forecast: forecastResponse.daily.map(toDailyForecast),
  };
}
