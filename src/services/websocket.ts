/**
 * SAWS WebSocket Client
 *
 * Real-time alerts and updates via WebSocket
 */

import { toast } from 'sonner';
import type { Alert } from '@/types';

/**
 * WebSocket message types
 */
export enum WSMessageType {
  ALERT = 'alert',
  ALERT_UPDATE = 'alert_update',
  WEATHER_UPDATE = 'weather_update',
  SATELLITE_UPDATE = 'satellite_update',
  DROUGHT_UPDATE = 'drought_update',
  PING = 'ping',
  PONG = 'pong',
}

/**
 * WebSocket message format
 */
export interface WSMessage<T = unknown> {
  type: WSMessageType;
  data: T;
  timestamp: string;
}

/**
 * Alert message data
 */
export interface WSAlertData {
  alert: {
    id: string;
    field_id?: string;
    severity: string;
    alert_type: string;
    title: string;
    message: string;
    district?: string;
    created_at: string;
  };
}

/**
 * Event handler type
 */
type EventHandler<T = unknown> = (data: T) => void;

/**
 * WebSocket client options
 */
export interface WSOptions {
  autoReconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  pingInterval?: number;
}

/**
 * WebSocket client for real-time updates
 */
export class WSClient {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectTimer: number | null = null;
  private pingTimer: number | null = null;
  private reconnectAttempts = 0;
  private isManualClose = false;

  private options: Required<WSOptions>;
  private handlers: Map<WSMessageType, Set<EventHandler>> = new Map();

  constructor(url: string, options: WSOptions = {}) {
    this.url = url;
    this.options = {
      autoReconnect: options.autoReconnect ?? true,
      reconnectInterval: options.reconnectInterval ?? 5000,
      maxReconnectAttempts: options.maxReconnectAttempts ?? 10,
      pingInterval: options.pingInterval ?? 30000,
    };
  }

  /**
   * Connect to WebSocket server
   */
  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return;
    }

    this.isManualClose = false;

    try {
      // Get auth token
      const token = localStorage.getItem('saws_token');

      // Build URL with auth token
      const wsUrl = new URL(this.url);
      if (token) {
        wsUrl.searchParams.set('token', token);
      }

      this.ws = new WebSocket(wsUrl.toString());

      this.ws.onopen = this.handleOpen.bind(this);
      this.ws.onmessage = this.handleMessage.bind(this);
      this.ws.onclose = this.handleClose.bind(this);
      this.ws.onerror = this.handleError.bind(this);
    } catch (error) {
      console.error('WebSocket connection error:', error);
      this.scheduleReconnect();
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    this.isManualClose = true;
    this.clearTimers();
    this.ws?.close();
    this.ws = null;
  }

  /**
   * Subscribe to message type
   */
  on<T = unknown>(type: WSMessageType, handler: EventHandler<T>): () => void {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, new Set());
    }
    this.handlers.get(type)!.add(handler);

    // Return unsubscribe function
    return () => {
      this.handlers.get(type)?.delete(handler);
    };
  }

  /**
   * Send message to server
   */
  send<T = unknown>(type: WSMessageType, data: T): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      const message: WSMessage<T> = {
        type,
        data,
        timestamp: new Date().toISOString(),
      };
      this.ws.send(JSON.stringify(message));
    }
  }

  /**
   * Get connection state
   */
  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  private handleOpen(): void {
    console.log('WebSocket connected');
    this.reconnectAttempts = 0;

    // Start ping interval
    this.startPing();
  }

  private handleMessage(event: MessageEvent): void {
    try {
      const message: WSMessage = JSON.parse(event.data);

      // Handle pong
      if (message.type === WSMessageType.PONG) {
        return;
      }

      // Handle ping
      if (message.type === WSMessageType.PING) {
        this.send(WSMessageType.PONG, {});
        return;
      }

      // Handle alerts
      if (message.type === WSMessageType.ALERT) {
        this.handleAlertMessage(message as WSMessage<WSAlertData>);
      }

      // Call registered handlers
      const handlers = this.handlers.get(message.type);
      handlers?.forEach((handler) => {
        try {
          handler(message.data);
        } catch (error) {
          console.error('Handler error:', error);
        }
      });
    } catch (error) {
      console.error('WebSocket message parse error:', error);
    }
  }

  private handleClose(): void {
    console.log('WebSocket closed');
    this.clearTimers();
    this.ws = null;

    if (!this.isManualClose && this.options.autoReconnect) {
      this.scheduleReconnect();
    }
  }

  private handleError(error: Event): void {
    console.error('WebSocket error:', error);
  }

  private handleAlertMessage(message: WSMessage<WSAlertData>): void {
    const alertData = message.data.alert;

    // Show toast notification
    switch (alertData.severity) {
      case 'critical':
        toast.error(alertData.title, {
          description: alertData.message,
          duration: 10000,
        });
        break;
      case 'warning':
        toast.warning(alertData.title, {
          description: alertData.message,
          duration: 7000,
        });
        break;
      default:
        toast.info(alertData.title, {
          description: alertData.message,
        });
    }

    // Play sound for critical alerts
    if (alertData.severity === 'critical') {
      this.playAlertSound();
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.options.maxReconnectAttempts) {
      console.error('Max reconnect attempts reached');
      return;
    }

    if (this.reconnectTimer !== null) {
      return;
    }

    this.reconnectTimer = window.setTimeout(() => {
      this.reconnectTimer = null;
      this.reconnectAttempts++;
      console.log(`Reconnecting... (attempt ${this.reconnectAttempts})`);
      this.connect();
    }, this.options.reconnectInterval);
  }

  private startPing(): void {
    this.clearTimers();
    this.pingTimer = window.setInterval(() => {
      this.send(WSMessageType.PING, {});
    }, this.options.pingInterval);
  }

  private clearTimers(): void {
    if (this.reconnectTimer !== null) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.pingTimer !== null) {
      clearInterval(this.pingTimer);
      this.pingTimer = null;
    }
  }

  private playAlertSound(): void {
    try {
      // Create audio context and play beep
      const audioContext = new AudioContext();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();

      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);

      oscillator.frequency.value = 800;
      oscillator.type = 'sine';
      gainNode.gain.value = 0.3;

      oscillator.start();
      oscillator.stop(audioContext.currentTime + 0.2);
    } catch (error) {
      // Audio not supported or blocked
    }
  }
}

/**
 * Create global WebSocket client instance
 *
 * Derives WebSocket URL from current page host for WSL compatibility
 * Falls back to environment variable if set
 */
const getWebSocketUrl = (): string => {
  if (import.meta.env.VITE_WS_URL) {
    return import.meta.env.VITE_WS_URL;
  }

  // Derive from current page's protocol and host
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = window.location.host; // e.g., "192.168.4.165:3000"
  const port = host.includes(':3000') ? ':8000' : ''; // Use backend port if frontend is on 3000

  return `${protocol}//${host.replace(':3000', ':8000')}/api/v1/ws/alerts`;
};

const WS_URL = getWebSocketUrl();
export const wsClient = new WSClient(WS_URL);

/**
 * Initialize WebSocket connection
 */
export function initWebSocket(): void {
  wsClient.connect();
}

/**
 * Close WebSocket connection
 */
export function closeWebSocket(): void {
  wsClient.disconnect();
}

/**
 * Subscribe to real-time alerts
 */
export function subscribeToAlerts(handler: (alert: Alert) => void): () => void {
  return wsClient.on<WSAlertData>(WSMessageType.ALERT, (data) => {
    handler({
      id: data.alert.id,
      fieldId: data.alert.field_id,
      severity: data.alert.severity as any,
      type: data.alert.alert_type as any,
      title: data.alert.title,
      message: data.alert.message,
      location: data.alert.district || 'Unknown',
      timestamp: new Date(data.alert.created_at),
      read: false,
      actionRequired: data.alert.severity === 'critical' || data.alert.severity === 'warning',
    });
  });
}

export default wsClient;
