/**
 * SAWS Alerts API Service
 *
 * API calls for alert management
 */

import { apiClient } from './api';
import type { PaginatedResponse, PaginationParams } from './api';
import type { Alert } from '@/types';

/**
 * Alert severity levels
 */
export type AlertSeverity = 'critical' | 'warning' | 'advisory' | 'info';

/**
 * Alert types
 */
export type AlertType =
  | 'drought'
  | 'low_ndvi'
  | 'soil_moisture'
  | 'extreme_temperature'
  | 'pest_detection'
  | 'irrigation_needed'
  | 'frost_warning'
  | 'harvest_ready';

/**
 * Alert creation data
 */
export interface AlertCreate {
  field_id?: string;
  severity: AlertSeverity;
  alert_type: AlertType;
  title: string;
  message: string;
  district?: string;
  priority?: number;
}

/**
 * Alert update data
 */
export interface AlertUpdate {
  title?: string;
  message?: string;
  priority?: number;
  is_read?: boolean;
}

/**
 * Alert detail (API format)
 */
export interface AlertDetail {
  id: string;
  user_id: string;
  field_id?: string;
  severity: AlertSeverity;
  alert_type: AlertType;
  title: string;
  message: string;
  district?: string;
  data?: Record<string, unknown>;
  is_read: boolean;
  read_at?: string;
  email_sent: boolean;
  sms_sent: boolean;
  whatsapp_sent: boolean;
  priority: number;
  created_at: string;
  expires_at?: string;
}

/**
 * List alerts with filters
 */
export async function listAlerts(
  params: PaginationParams & {
    severity?: AlertSeverity;
    is_read?: boolean;
    field_id?: string;
  } = {}
): Promise<PaginatedResponse<AlertDetail>> {
  return apiClient.get('/alerts', { params });
}

/**
 * Get alert details
 */
export async function getAlert(alertId: string): Promise<AlertDetail> {
  return apiClient.get(`/alerts/${alertId}`);
}

/**
 * Create a new alert
 */
export async function createAlert(data: AlertCreate): Promise<AlertDetail> {
  return apiClient.post('/alerts', data);
}

/**
 * Update an alert
 */
export async function updateAlert(alertId: string, data: AlertUpdate): Promise<AlertDetail> {
  return apiClient.put(`/alerts/${alertId}`, data);
}

/**
 * Mark alert as read
 */
export async function markAlertRead(alertId: string): Promise<AlertDetail> {
  return apiClient.put(`/alerts/${alertId}/read`);
}

/**
 * Mark alert as unread
 */
export async function markAlertUnread(alertId: string): Promise<AlertDetail> {
  return apiClient.put(`/alerts/${alertId}/unread`);
}

/**
 * Delete an alert
 */
export async function deleteAlert(alertId: string): Promise<void> {
  return apiClient.delete(`/alerts/${alertId}`);
}

/**
 * Get unread alert count
 */
export async function getUnreadCount(): Promise<number> {
  const response = await listAlerts({ is_read: false, limit: 1 });
  return response.total;
}

/**
 * Convert API alert to frontend format
 * Note: Alert interface now matches API response format, so minimal conversion needed
 */
export function toAlert(detail: AlertDetail): Alert {
  return {
    id: detail.id,
    user_id: detail.user_id,
    field_id: detail.field_id,
    severity: detail.severity,
    alert_type: detail.alert_type,
    title: detail.title,
    message: detail.message,
    district: detail.district,
    priority: detail.priority,
    data: detail.data,
    is_read: detail.is_read,
    read_at: detail.read_at,
    email_sent: detail.email_sent,
    sms_sent: detail.sms_sent,
    whatsapp_sent: detail.whatsapp_sent,
    created_at: detail.created_at,
    expires_at: detail.expires_at,
  };
}

/**
 * Convert paginated alerts to frontend format
 */
export function toAlertList(
  response: PaginatedResponse<AlertDetail>
): { total: number; skip: number; limit: number; items: Alert[] } {
  return {
    total: response.total,
    skip: response.skip || 0,
    limit: response.limit || 20,
    items: response.items.map(toAlert),
  };
}
