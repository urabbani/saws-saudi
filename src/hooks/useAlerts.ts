/**
 * useAlerts Hook
 *
 * Custom hook for fetching and managing alerts
 */

import { useEffect, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  listAlerts,
  getAlert,
  markAlertRead,
  markAlertUnread,
  deleteAlert,
  getUnreadCount,
  toAlertList,
  type AlertDetail,
  type AlertUpdate,
} from '@/services/alerts';
import { initWebSocket, closeWebSocket, subscribeToAlerts } from '@/services/websocket';
import type { Alert } from '@/types';

/**
 * Query keys for alert-related queries
 */
export const alertKeys = {
  all: ['alerts'] as const,
  lists: () => [...alertKeys.all, 'list'] as const,
  list: (filters: Record<string, unknown>) => [...alertKeys.lists(), filters] as const,
  details: () => [...alertKeys.all, 'detail'] as const,
  detail: (id: string) => [...alertKeys.details(), id] as const,
  unreadCount: () => [...alertKeys.all, 'unreadCount'] as const,
};

/**
 * Hook to fetch paginated list of alerts
 */
export function useAlerts(
  params: {
    skip?: number;
    limit?: number;
    severity?: string;
    is_read?: boolean;
    field_id?: string;
  } = {}
) {
  return useQuery({
    queryKey: alertKeys.list(params),
    queryFn: () => listAlerts(params),
    select: toAlertList,
    staleTime: 1 * 60 * 1000, // 1 minute
    refetchInterval: 30 * 1000, // Refetch every 30 seconds
  });
}

/**
 * Hook to fetch a single alert by ID
 */
export function useAlert(alertId: string | null) {
  return useQuery({
    queryKey: alertKeys.detail(alertId || ''),
    queryFn: () => getAlert(alertId!),
    enabled: !!alertId,
    select: (data): Alert => ({
      id: data.id,
      fieldId: data.field_id,
      severity: data.severity as any,
      type: data.alert_type as any,
      title: data.title,
      message: data.message,
      location: data.district || 'Unknown',
      timestamp: new Date(data.created_at),
      read: data.is_read,
      actionRequired: data.severity === 'critical' || data.severity === 'warning',
      metadata: data.data,
    }),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to fetch unread alert count
 */
export function useUnreadAlertCount() {
  return useQuery({
    queryKey: alertKeys.unreadCount(),
    queryFn: getUnreadCount,
    staleTime: 1 * 60 * 1000, // 1 minute
    refetchInterval: 30 * 1000, // Refetch every 30 seconds
  });
}

/**
 * Hook to mark alert as read
 */
export function useMarkAlertRead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (alertId: string) => markAlertRead(alertId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: alertKeys.lists() });
      queryClient.invalidateQueries({ queryKey: alertKeys.unreadCount() });
    },
  });
}

/**
 * Hook to mark alert as unread
 */
export function useMarkAlertUnread() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (alertId: string) => markAlertUnread(alertId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: alertKeys.lists() });
      queryClient.invalidateQueries({ queryKey: alertKeys.unreadCount() });
    },
  });
}

/**
 * Hook to delete an alert
 */
export function useDeleteAlert() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (alertId: string) => deleteAlert(alertId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: alertKeys.lists() });
      queryClient.invalidateQueries({ queryKey: alertKeys.unreadCount() });
      toast.success('Alert deleted');
    },
  });
}

/**
 * Hook to mark all alerts as read
 */
export function useMarkAllRead() {
  const queryClient = useQueryClient();
  const { data: alerts } = useAlerts({ is_read: false, limit: 100 });
  const markRead = useMarkAlertRead();

  return useMutation({
    mutationFn: async () => {
      const unreadIds = alerts?.items
        .filter((a) => !a.read)
        .map((a) => a.id) || [];
      await Promise.all(unreadIds.map((id) => markRead.mutateAsync(id)));
    },
    onSuccess: () => {
      toast.success('All alerts marked as read');
    },
  });
}

/**
 * Hook to get critical alerts
 */
export function useCriticalAlerts() {
  return useQuery({
    queryKey: alertKeys.list({ severity: 'critical', is_read: false }),
    queryFn: () => listAlerts({ severity: 'critical' as any, is_read: false, limit: 10 }),
    select: toAlertList,
    staleTime: 1 * 60 * 1000,
    refetchInterval: 30 * 1000,
  });
}

/**
 * Hook for real-time alerts via WebSocket
 *
 * Note: WebSocket endpoint not yet implemented in backend
 * This hook safely handles connection failures
 */
export function useRealtimeAlerts(onNewAlert?: (alert: Alert) => void) {
  const queryClient = useQueryClient();

  useEffect(() => {
    // Only initialize WebSocket if explicitly enabled via environment variable
    const wsEnabled = import.meta.env.VITE_ENABLE_WEBSOCKET === 'true';

    if (!wsEnabled) {
      return;
    }

    // Initialize WebSocket connection
    try {
      initWebSocket();
    } catch (error) {
      console.warn('WebSocket initialization disabled - backend endpoint not implemented');
      return;
    }

    // Subscribe to new alerts
    const unsubscribe = subscribeToAlerts((alert) => {
      // Invalidate queries to fetch new alerts
      queryClient.invalidateQueries({ queryKey: alertKeys.lists() });
      queryClient.invalidateQueries({ queryKey: alertKeys.unreadCount() });

      // Call custom handler
      if (onNewAlert) {
        onNewAlert(alert);
      }
    });

    // Cleanup on unmount
    return () => {
      unsubscribe();
      closeWebSocket();
    };
  }, [queryClient, onNewAlert]);

  return {
    isConnected: false, // TODO: Check wsClient.isConnected when endpoint is implemented
  };
}

/**
 * Combined hook for alert management
 */
export function useAlertsManager() {
  const { data: alerts, isLoading, error } = useAlerts({ limit: 50 });
  const { data: unreadCount } = useUnreadAlertCount();
  const { data: criticalAlerts } = useCriticalAlerts();
  const markRead = useMarkAlertRead();
  const markUnread = useMarkAlertUnread();
  const deleteAlert = useDeleteAlert();
  const markAllRead = useMarkAllRead();

  return {
    alerts: alerts?.items || [],
    totalAlerts: alerts?.total || 0,
    unreadCount: unreadCount || 0,
    criticalAlerts: criticalAlerts?.items || [],
    isLoading,
    error,
    markRead: markRead.mutate,
    markUnread: markUnread.mutate,
    deleteAlert: deleteAlert.mutate,
    markAllRead: markAllRead.mutate,
  };
}
