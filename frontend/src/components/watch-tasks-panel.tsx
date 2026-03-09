import { useState, useEffect } from 'react';
import { Eye, Plus, Trash2, ToggleLeft, ToggleRight, Clock } from 'lucide-react';
import type { WatchTask, WatchTaskEvent } from '../api/client';
import api from '../api/client';

const DAYS_LABELS = ['א', 'ב', 'ג', 'ד', 'ה', 'ו', 'ש'];

export function WatchTasksPanel() {
  const [tasks, setTasks] = useState<WatchTask[]>([]);
  const [events, setEvents] = useState<WatchTaskEvent[]>([]);
  const [isAdding, setIsAdding] = useState(false);
  const [newLabel, setNewLabel] = useState('');
  const [newDescription, setNewDescription] = useState('');
  const [newStartTime, setNewStartTime] = useState('00:00');
  const [newEndTime, setNewEndTime] = useState('23:59');
  const [newDays, setNewDays] = useState('0,1,2,3,4,5,6');
  const [newCooldown, setNewCooldown] = useState(60);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 8000);
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const [tasksRes, eventsRes] = await Promise.all([
        api.getWatchTasks(),
        api.getWatchTaskEvents(10),
      ]);
      setTasks(tasksRes.data);
      setEvents(eventsRes.data);
    } catch {
      // silent
    }
  };

  const handleAdd = async () => {
    if (!newLabel || !newDescription) return;
    try {
      await api.createWatchTask({
        label: newLabel,
        description: newDescription,
        days_of_week: newDays,
        start_time: newStartTime,
        end_time: newEndTime,
        cooldown_seconds: newCooldown,
      });
      setNewLabel('');
      setNewDescription('');
      setNewStartTime('00:00');
      setNewEndTime('23:59');
      setIsAdding(false);
      loadData();
    } catch {
      // silent
    }
  };

  const handleToggle = async (task: WatchTask) => {
    try {
      await api.updateWatchTask(task.id, { is_enabled: !task.is_enabled });
      loadData();
    } catch {
      // silent
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await api.deleteWatchTask(id);
      loadData();
    } catch {
      // silent
    }
  };

  const toggleDay = (dayIndex: number) => {
    const currentDays = newDays.split(',').filter(Boolean);
    const dayStr = String(dayIndex);
    if (currentDays.includes(dayStr)) {
      setNewDays(currentDays.filter(d => d !== dayStr).join(','));
    } else {
      setNewDays([...currentDays, dayStr].sort().join(','));
    }
  };

  return (
    <div style={{ background: '#111', borderLeft: '1px solid #1a1a1a' }}>
      <div className="flex items-center justify-between px-3 py-2" style={{ borderBottom: '1px solid #1a1a1a' }}>
        <div className="flex items-center gap-2">
          <Eye size={14} style={{ color: '#ffaa00' }} />
          <span className="text-xs tracking-wider" style={{ color: '#888' }}>משימות ניטור</span>
        </div>
        <button onClick={() => setIsAdding(!isAdding)} style={{ color: '#00ff88' }}>
          <Plus size={14} />
        </button>
      </div>

      {isAdding && (
        <div className="p-3 space-y-2" style={{ borderBottom: '1px solid #1a1a1a' }}>
          <input
            type="text" value={newLabel} onChange={(e) => setNewLabel(e.target.value)}
            placeholder="שם המשימה"
            className="w-full px-2 py-1 text-xs outline-none"
            style={{ background: '#0a0a0a', border: '1px solid #2a2a2a', color: '#e0e0e0' }}
          />
          <textarea
            value={newDescription} onChange={(e) => setNewDescription(e.target.value)}
            placeholder="מה לחפש? (תיאור חופשי)"
            rows={2}
            className="w-full px-2 py-1 text-xs outline-none resize-none"
            style={{ background: '#0a0a0a', border: '1px solid #2a2a2a', color: '#e0e0e0' }}
          />
          <div className="flex gap-2 items-center">
            <Clock size={12} style={{ color: '#555' }} />
            <input
              type="time" value={newStartTime} onChange={(e) => setNewStartTime(e.target.value)}
              className="px-1 py-0.5 text-xs outline-none"
              style={{ background: '#0a0a0a', border: '1px solid #2a2a2a', color: '#e0e0e0' }}
            />
            <span className="text-xs" style={{ color: '#555' }}>עד</span>
            <input
              type="time" value={newEndTime} onChange={(e) => setNewEndTime(e.target.value)}
              className="px-1 py-0.5 text-xs outline-none"
              style={{ background: '#0a0a0a', border: '1px solid #2a2a2a', color: '#e0e0e0' }}
            />
          </div>
          <div className="flex gap-1">
            {DAYS_LABELS.map((label, idx) => (
              <button
                key={idx} onClick={() => toggleDay(idx)}
                className="w-6 h-6 text-xs flex items-center justify-center"
                style={{
                  background: newDays.split(',').includes(String(idx)) ? '#1a2a1a' : '#0a0a0a',
                  border: `1px solid ${newDays.split(',').includes(String(idx)) ? '#00ff88' : '#2a2a2a'}`,
                  color: newDays.split(',').includes(String(idx)) ? '#00ff88' : '#555',
                }}
              >
                {label}
              </button>
            ))}
          </div>
          <div className="flex gap-2 items-center">
            <span className="text-xs" style={{ color: '#555' }}>cooldown:</span>
            <select
              value={newCooldown} onChange={(e) => setNewCooldown(Number(e.target.value))}
              className="px-1 py-0.5 text-xs outline-none"
              style={{ background: '#0a0a0a', border: '1px solid #2a2a2a', color: '#e0e0e0' }}
            >
              <option value={30}>30 שניות</option>
              <option value={60}>דקה</option>
              <option value={120}>2 דקות</option>
              <option value={300}>5 דקות</option>
            </select>
          </div>
          <button
            onClick={handleAdd}
            className="w-full py-1 text-xs tracking-wider"
            style={{ background: '#ffaa00', color: '#0a0a0a' }}
          >
            הוסף משימה
          </button>
        </div>
      )}

      <div className="px-3 py-2 space-y-2">
        {tasks.map((task) => (
          <div
            key={task.id}
            className="py-1 px-2"
            style={{ background: '#0a0a0a', border: '1px solid #1a1a1a' }}
          >
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <p className="text-xs font-bold" style={{ color: task.is_enabled ? '#ffaa00' : '#555' }}>
                  {task.label}
                </p>
                <p className="text-xs" style={{ color: '#666', fontSize: '10px' }}>
                  {task.description.length > 50 ? task.description.substring(0, 50) + '...' : task.description}
                </p>
                <p className="text-xs" style={{ color: '#444', fontSize: '9px' }}>
                  {task.start_time}–{task.end_time} | התאמות: {task.total_matches}
                </p>
              </div>
              <div className="flex items-center gap-1">
                <button onClick={() => handleToggle(task)} style={{ color: task.is_enabled ? '#00ff88' : '#555' }}>
                  {task.is_enabled ? <ToggleRight size={16} /> : <ToggleLeft size={16} />}
                </button>
                <button onClick={() => handleDelete(task.id)} style={{ color: '#ff3333' }}>
                  <Trash2 size={12} />
                </button>
              </div>
            </div>
          </div>
        ))}
        {tasks.length === 0 && (
          <p className="text-xs text-center py-2" style={{ color: '#444' }}>אין משימות מוגדרות</p>
        )}
      </div>

      {events.length > 0 && (
        <div className="px-3 py-2" style={{ borderTop: '1px solid #1a1a1a' }}>
          <p className="text-xs mb-2 tracking-wider" style={{ color: '#555' }}>התאמות אחרונות</p>
          {events.slice(0, 5).map((evt) => (
            <div key={evt.id} className="py-1 text-xs" style={{ borderBottom: '1px solid #1a1a1a' }}>
              <span className="px-1" style={{
                background: evt.confidence === 'high' ? '#2a1a0a' : '#1a1a1a',
                color: evt.confidence === 'high' ? '#ffaa00' : '#888',
                fontSize: '10px',
              }}>
                {evt.confidence}
              </span>
              <span style={{ color: '#e0e0e0' }}> {evt.match_description.substring(0, 80)}</span>
              <span className="block" style={{ color: '#333', fontSize: '10px' }}>
                {new Date(evt.created_at).toLocaleString('he-IL')}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
