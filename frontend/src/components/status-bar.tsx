import { useEffect, useState } from 'react';
import { Activity, Clock, Database, Wifi, WifiOff } from 'lucide-react';
import type { CameraStatus, HealthInfo } from '../api/client';
import api from '../api/client';

export function StatusBar() {
  const [camera, setCamera] = useState<CameraStatus | null>(null);
  const [health, setHealth] = useState<HealthInfo | null>(null);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const [camRes, healthRes] = await Promise.all([
          api.getCameraStatus(),
          api.getHealth(),
        ]);
        setCamera(camRes.data);
        setHealth(healthRes.data);
      } catch {
        // silent fail
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const formatUptime = (seconds: number | null): string => {
    if (!seconds) return '--:--:--';
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  };

  return (
    <div
      className="flex items-center gap-6 px-4 py-2 text-xs tracking-wider"
      style={{ background: '#111', borderBottom: '1px solid #1a1a1a' }}
    >
      <StatusChip
        icon={camera?.status === 'connected' ? <Wifi size={12} /> : <WifiOff size={12} />}
        label="CAMERA"
        value={camera?.status?.toUpperCase() || 'UNKNOWN'}
        isOk={camera?.status === 'connected'}
      />
      <StatusChip
        icon={<Clock size={12} />}
        label="UPTIME"
        value={formatUptime(health?.uptime_seconds ?? null)}
        isOk={true}
      />
      <StatusChip
        icon={<Activity size={12} />}
        label="CAM UPTIME"
        value={formatUptime(camera?.uptime_seconds ?? null)}
        isOk={camera?.status === 'connected'}
      />
      <StatusChip
        icon={<Database size={12} />}
        label="BUFFER"
        value={String(camera?.buffer_size ?? 0)}
        isOk={true}
      />
    </div>
  );
}

function StatusChip({
  icon,
  label,
  value,
  isOk,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  isOk: boolean;
}) {
  return (
    <div className="flex items-center gap-2">
      <span style={{ color: isOk ? '#00ff88' : '#ff3333' }}>{icon}</span>
      <span style={{ color: '#555' }}>{label}</span>
      <span style={{ color: isOk ? '#e0e0e0' : '#ff3333' }}>{value}</span>
    </div>
  );
}
