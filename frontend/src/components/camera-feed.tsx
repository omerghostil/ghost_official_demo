import { useState } from 'react';
import { Camera, CameraOff, RefreshCw } from 'lucide-react';
import api from '../api/client';

export function CameraFeed() {
  const [hasError, setHasError] = useState(false);
  const streamUrl = '/camera/stream';

  const handleReconnect = async () => {
    try {
      await api.reconnectCamera();
      setHasError(false);
    } catch {
      // reconnect failed silently
    }
  };

  return (
    <div className="relative w-full" style={{ background: '#000' }}>
      {hasError ? (
        <div
          className="flex flex-col items-center justify-center"
          style={{ minHeight: '400px', color: '#555' }}
        >
          <CameraOff size={48} strokeWidth={1} />
          <p className="mt-3 text-sm tracking-wider">NO SIGNAL</p>
          <button
            onClick={handleReconnect}
            className="mt-4 flex items-center gap-2 px-4 py-2 text-xs tracking-wider"
            style={{ border: '1px solid #2a2a2a', color: '#888' }}
          >
            <RefreshCw size={14} /> RECONNECT
          </button>
        </div>
      ) : (
        <img
          src={streamUrl}
          alt="Live Camera Feed"
          className="w-full"
          style={{ filter: 'grayscale(100%) contrast(1.2)', minHeight: '400px', objectFit: 'cover' }}
          onError={() => setHasError(true)}
        />
      )}
      <div
        className="absolute top-3 left-3 flex items-center gap-2 px-2 py-1"
        style={{ background: 'rgba(0,0,0,0.7)' }}
      >
        <div
          className="w-2 h-2 rounded-full pulse-green"
          style={{ background: hasError ? '#ff3333' : '#00ff88' }}
        />
        <span className="text-xs tracking-wider" style={{ color: '#888' }}>
          {hasError ? 'OFFLINE' : 'LIVE'}
        </span>
      </div>
    </div>
  );
}
