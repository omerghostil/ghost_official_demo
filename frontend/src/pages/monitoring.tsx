import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { LogOut, Settings } from 'lucide-react';
import { useAuthStore } from '../store/auth-store';
import { CameraFeed } from '../components/camera-feed';
import { StatusBar } from '../components/status-bar';
import { ChatPanel } from '../components/chat-panel';
import { AlertsPanel } from '../components/alerts-panel';
import { MemoryPanel } from '../components/memory-panel';
import { WatchTasksPanel } from '../components/watch-tasks-panel';

export function MonitoringPage() {
  const { user, isAuthenticated, logout } = useAuthStore();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
    }
  }, [isAuthenticated, navigate]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  if (!isAuthenticated) return null;

  return (
    <div className="min-h-screen flex flex-col" style={{ background: '#0a0a0a' }}>
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 py-2"
        style={{ background: '#0a0a0a', borderBottom: '1px solid #1a1a1a' }}
      >
        <div className="flex items-center gap-3">
          <span className="text-sm font-bold tracking-widest" style={{ color: '#00ff88' }}>
            GHOST BRAIN
          </span>
          <span className="text-xs tracking-wider" style={{ color: '#333' }}>
            DEMO v1.0
          </span>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-xs" style={{ color: '#555' }}>
            {user?.username} [{user?.role}]
          </span>
          {user?.role === 'admin' && (
            <button
              onClick={() => navigate('/admin')}
              className="flex items-center gap-1 text-xs"
              style={{ color: '#888' }}
            >
              <Settings size={12} /> ADMIN
            </button>
          )}
          <button
            onClick={handleLogout}
            className="flex items-center gap-1 text-xs"
            style={{ color: '#888' }}
          >
            <LogOut size={12} /> EXIT
          </button>
        </div>
      </div>

      <StatusBar />

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Camera Feed - Center */}
        <div className="flex-1 flex flex-col">
          <CameraFeed />
          <div style={{ background: '#111', borderTop: '1px solid #1a1a1a' }}>
            <MemoryPanel />
          </div>
        </div>

        {/* Side Panel - Right */}
        <div className="flex flex-col" style={{ width: '360px' }}>
          <div className="flex-1 overflow-y-auto">
            <WatchTasksPanel />
            <AlertsPanel />
            <ChatPanel />
          </div>
        </div>
      </div>
    </div>
  );
}
