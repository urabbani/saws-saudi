import { useState, useEffect, useCallback } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import './App.css';
import { Header } from '@/sections/Header';
import { DashboardOverview } from '@/sections/DashboardOverview';
import { UnifiedMapViewer } from '@/sections/UnifiedMapViewer';
import { CropHealthMonitor } from '@/sections/CropHealthMonitor';
import { SatelliteSources } from '@/sections/SatelliteSources';
import { AnalyticsPanel } from '@/sections/AnalyticsPanel';
import { AlertsPanel } from '@/sections/AlertsPanel';
import { WeatherWidget } from '@/sections/WeatherWidget';
import { FieldDetailModal } from '@/sections/FieldDetailModal';
import { alerts as initialAlerts } from '@/data/mockData';
import type { FieldData, Alert } from '@/types';
import { Toaster } from '@/components/ui/sonner';
import { useRealtimeAlerts } from '@/hooks';

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 1,
    },
  },
});

function AppContent() {
  const [selectedField, setSelectedField] = useState<FieldData | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>(initialAlerts);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [isLoading, setIsLoading] = useState(true);

  // Initialize real-time alerts via WebSocket
  useRealtimeAlerts((newAlert) => {
    setAlerts(prev => [newAlert, ...prev].slice(0, 50)); // Keep last 50 alerts
  });

  // Simulate initial loading
  useEffect(() => {
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 1000);
    return () => clearTimeout(timer);
  }, []);

  // Simulate real-time alert updates
  useEffect(() => {
    const interval = setInterval(() => {
      // Randomly mark alerts as read after some time
      setAlerts(prev => prev.map(alert =>
        !alert.is_read && Math.random() > 0.95 ? { ...alert, is_read: true } : alert
      ));
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleFieldSelect = useCallback((field: FieldData) => {
    setSelectedField(field);
  }, []);

  const handleAlertDismiss = useCallback((alertId: string) => {
    setAlerts(prev => prev.filter(a => a.id !== alertId));
  }, []);

  const handleAlertRead = useCallback((alertId: string) => {
    setAlerts(prev => prev.map(a =>
      a.id === alertId ? { ...a, is_read: true } : a
    ));
  }, []);

  const unreadAlertsCount = alerts.filter(a => !a.is_read).length;

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: 'rgba(253, 246, 227, 0.5)' }}>
        <div className="text-center">
          <div className="spinner mx-auto mb-4"></div>
          <h2 className="text-xl font-semibold text-gray-700">Loading Saudi AgriDrought Warning System...</h2>
          <p className="text-sm text-gray-500 mt-2">Initializing GIS Dashboard</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col" style={{ backgroundColor: 'rgba(253, 246, 227, 0.4)' }}>
      <Header 
        activeTab={activeTab} 
        onTabChange={setActiveTab}
        unreadAlertsCount={unreadAlertsCount}
      />
      
      <main className="flex-1 p-4 lg:p-6 overflow-auto">
        <div className="max-w-[1920px] mx-auto space-y-6">
          {/* Dashboard Overview - KPI Cards */}
          <DashboardOverview />

          {/* Main Content Grid */}
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
            {/* GIS Map - Takes up 2/3 on large screens */}
            <div className="xl:col-span-2 space-y-6">
              <UnifiedMapViewer onFieldSelect={handleFieldSelect} />
              <CropHealthMonitor />
              <SatelliteSources />
            </div>

            {/* Sidebar - Takes up 1/3 on large screens */}
            <div className="space-y-6">
              <WeatherWidget />
              <AlertsPanel
                alerts={alerts}
                onDismiss={handleAlertDismiss}
                onRead={handleAlertRead}
              />
              <AnalyticsPanel />
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 py-4 px-6">
        <div className="max-w-[1920px] mx-auto flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="text-sm text-gray-500">
            © 2025 Saudi AgriDrought Warning System. All rights reserved.
          </div>
          <div className="flex items-center gap-6 text-sm text-gray-500">
            <span>Powered by:</span>
            <div className="flex items-center gap-4">
              <span className="hover:text-primary-medium cursor-pointer transition-colors">NASA</span>
              <span className="hover:text-primary-medium cursor-pointer transition-colors">ESA</span>
              <span className="hover:text-primary-medium cursor-pointer transition-colors">USGS</span>
              <span className="hover:text-primary-medium cursor-pointer transition-colors">Planet</span>
            </div>
          </div>
          <div className="flex items-center gap-4 text-sm">
            <a href="#" className="text-gray-500 hover:text-primary-medium transition-colors">Privacy Policy</a>
            <a href="#" className="text-gray-500 hover:text-primary-medium transition-colors">Terms</a>
            <a href="#" className="text-gray-500 hover:text-primary-medium transition-colors">API Docs</a>
          </div>
        </div>
      </footer>

      {/* Field Detail Modal */}
      {selectedField && (
        <FieldDetailModal 
          field={selectedField}
          onClose={() => setSelectedField(null)}
        />
      )}

      <Toaster position="top-right" />
    </div>
  );
}

// Wrapper component with QueryClientProvider
function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  );
}

export default App;
