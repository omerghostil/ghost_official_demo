import { useState, useEffect } from 'react';
import { AlertTriangle, Plus, Trash2, ToggleLeft, ToggleRight } from 'lucide-react';
import type { AlertRule, AlertEvent } from '../api/client';
import api from '../api/client';

export function AlertsPanel() {
  const [rules, setRules] = useState<AlertRule[]>([]);
  const [events, setEvents] = useState<AlertEvent[]>([]);
  const [isAdding, setIsAdding] = useState(false);
  const [newLabel, setNewLabel] = useState('');
  const [newTarget, setNewTarget] = useState('');
  const [hasFlash, setHasFlash] = useState(false);
  const [prevEventCount, setPrevEventCount] = useState(0);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (events.length > prevEventCount && prevEventCount > 0) {
      setHasFlash(true);
      setTimeout(() => setHasFlash(false), 2000);
    }
    setPrevEventCount(events.length);
  }, [events.length]);

  const loadData = async () => {
    try {
      const [rulesRes, eventsRes] = await Promise.all([
        api.getAlertRules(),
        api.getAlertEvents(10),
      ]);
      setRules(rulesRes.data);
      setEvents(eventsRes.data);
    } catch {
      // silent
    }
  };

  const handleAdd = async () => {
    if (!newLabel || !newTarget) return;
    try {
      await api.createAlertRule({
        label: newLabel,
        target_text: newTarget,
        days_of_week: '0,1,2,3,4,5,6',
        start_time: '00:00',
        end_time: '23:59',
        cooldown_seconds: 300,
      });
      setNewLabel('');
      setNewTarget('');
      setIsAdding(false);
      loadData();
    } catch {
      // silent
    }
  };

  const handleToggle = async (rule: AlertRule) => {
    try {
      await api.updateAlertRule(rule.id, { is_enabled: !rule.is_enabled });
      loadData();
    } catch {
      // silent
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await api.deleteAlertRule(id);
      loadData();
    } catch {
      // silent
    }
  };

  return (
    <div className={`${hasFlash ? 'alert-flash' : ''}`} style={{ background: '#111', borderLeft: '1px solid #1a1a1a' }}>
      <div className="flex items-center justify-between px-3 py-2" style={{ borderBottom: '1px solid #1a1a1a' }}>
        <div className="flex items-center gap-2">
          <AlertTriangle size={14} style={{ color: '#ff3333' }} />
          <span className="text-xs tracking-wider" style={{ color: '#888' }}>CRITICAL ALERTS</span>
        </div>
        {rules.length < 4 && (
          <button onClick={() => setIsAdding(!isAdding)} style={{ color: '#00ff88' }}>
            <Plus size={14} />
          </button>
        )}
      </div>

      {isAdding && (
        <div className="p-3 space-y-2" style={{ borderBottom: '1px solid #1a1a1a' }}>
          <input
            type="text"
            value={newLabel}
            onChange={(e) => setNewLabel(e.target.value)}
            placeholder="Rule label"
            className="w-full px-2 py-1 text-xs outline-none"
            style={{ background: '#0a0a0a', border: '1px solid #2a2a2a', color: '#e0e0e0' }}
          />
          <input
            type="text"
            value={newTarget}
            onChange={(e) => setNewTarget(e.target.value)}
            placeholder="Alert if detected..."
            className="w-full px-2 py-1 text-xs outline-none"
            style={{ background: '#0a0a0a', border: '1px solid #2a2a2a', color: '#e0e0e0' }}
          />
          <button
            onClick={handleAdd}
            className="w-full py-1 text-xs tracking-wider"
            style={{ background: '#00ff88', color: '#0a0a0a' }}
          >
            ADD RULE
          </button>
        </div>
      )}

      <div className="px-3 py-2 space-y-2">
        {rules.map((rule) => (
          <div
            key={rule.id}
            className="flex items-center justify-between py-1 px-2"
            style={{ background: '#0a0a0a', border: '1px solid #1a1a1a' }}
          >
            <div className="flex-1">
              <p className="text-xs" style={{ color: rule.is_enabled ? '#e0e0e0' : '#555' }}>
                {rule.label}
              </p>
              <p className="text-xs" style={{ color: '#444', fontSize: '10px' }}>
                {rule.target_text}
              </p>
            </div>
            <div className="flex items-center gap-1">
              <button onClick={() => handleToggle(rule)} style={{ color: rule.is_enabled ? '#00ff88' : '#555' }}>
                {rule.is_enabled ? <ToggleRight size={16} /> : <ToggleLeft size={16} />}
              </button>
              <button onClick={() => handleDelete(rule.id)} style={{ color: '#ff3333' }}>
                <Trash2 size={12} />
              </button>
            </div>
          </div>
        ))}
        {rules.length === 0 && (
          <p className="text-xs text-center py-2" style={{ color: '#444' }}>No rules defined</p>
        )}
      </div>

      {events.length > 0 && (
        <div className="px-3 py-2" style={{ borderTop: '1px solid #1a1a1a' }}>
          <p className="text-xs mb-2 tracking-wider" style={{ color: '#555' }}>RECENT ALERTS</p>
          {events.slice(0, 5).map((evt) => (
            <div
              key={evt.id}
              className="py-1 text-xs"
              style={{ borderBottom: '1px solid #1a1a1a' }}
            >
              <span style={{ color: '#ff3333' }}>{evt.severity.toUpperCase()}</span>
              <span style={{ color: '#555' }}> — </span>
              <span style={{ color: '#e0e0e0' }}>{evt.match_text || 'match'}</span>
              <span className="block" style={{ color: '#333', fontSize: '10px' }}>
                {new Date(evt.created_at).toLocaleString()}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
