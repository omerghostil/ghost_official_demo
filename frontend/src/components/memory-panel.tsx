import { useEffect, useState } from 'react';
import { Brain } from 'lucide-react';
import type { MemoryEntry } from '../api/client';
import api from '../api/client';

export function MemoryPanel() {
  const [entries, setEntries] = useState<MemoryEntry[]>([]);

  useEffect(() => {
    loadMemory();
    const interval = setInterval(loadMemory, 10000);
    return () => clearInterval(interval);
  }, []);

  const loadMemory = async () => {
    try {
      const { data } = await api.getMemory({ query: undefined });
      setEntries(data);
    } catch {
      // silent
    }
  };

  return (
    <div>
      <div className="flex items-center gap-2 px-3 py-2" style={{ borderBottom: '1px solid #1a1a1a' }}>
        <Brain size={14} style={{ color: '#00ff88' }} />
        <span className="text-xs tracking-wider" style={{ color: '#888' }}>MEMORY</span>
        <span className="text-xs" style={{ color: '#444' }}>({entries.length})</span>
      </div>
      <div className="px-3 py-2 space-y-2 overflow-y-auto" style={{ maxHeight: '250px' }}>
        {entries.length === 0 ? (
          <p className="text-xs text-center py-4" style={{ color: '#444' }}>
            Memory is building...
          </p>
        ) : (
          entries.map((entry) => (
            <div
              key={entry.id}
              className="px-2 py-2"
              style={{ background: '#0a0a0a', border: '1px solid #1a1a1a' }}
            >
              <div className="flex items-center gap-2 mb-1">
                <span style={{ color: '#555', fontSize: '10px' }}>
                  {new Date(entry.timestamp_start).toLocaleTimeString()}
                  {' — '}
                  {new Date(entry.timestamp_end).toLocaleTimeString()}
                </span>
                {entry.people_count > 0 && (
                  <span className="px-1" style={{ background: '#1a2a1a', color: '#00ff88', fontSize: '10px' }}>
                    {entry.people_count}P
                  </span>
                )}
                {entry.vehicle_count > 0 && (
                  <span className="px-1" style={{ background: '#1a1a2a', color: '#8888ff', fontSize: '10px' }}>
                    {entry.vehicle_count}V
                  </span>
                )}
              </div>
              <p className="text-xs leading-relaxed" style={{ color: '#ccc' }}>
                {entry.text_summary.length > 200
                  ? entry.text_summary.substring(0, 200) + '...'
                  : entry.text_summary}
              </p>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
