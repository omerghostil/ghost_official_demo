import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Users, Activity, HardDrive, UserPlus, Trash2, ToggleLeft, ToggleRight } from 'lucide-react';
import { useAuthStore } from '../store/auth-store';
import type { UserInfo, WorkersHealth, StorageHealth, HealthInfo } from '../api/client';
import api from '../api/client';

export function AdminPage() {
  const { user, isAuthenticated } = useAuthStore();
  const navigate = useNavigate();

  const [users, setUsers] = useState<UserInfo[]>([]);
  const [workers, setWorkers] = useState<WorkersHealth | null>(null);
  const [storage, setStorage] = useState<StorageHealth | null>(null);
  const [health, setHealth] = useState<HealthInfo | null>(null);

  const [showAddUser, setShowAddUser] = useState(false);
  const [newUsername, setNewUsername] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newRole, setNewRole] = useState('client');

  useEffect(() => {
    if (!isAuthenticated || user?.role !== 'admin') {
      navigate('/');
      return;
    }
    loadAll();
    const interval = setInterval(loadAll, 10000);
    return () => clearInterval(interval);
  }, [isAuthenticated, user]);

  const loadAll = async () => {
    try {
      const [usersRes, workersRes, storageRes, healthRes] = await Promise.all([
        api.getUsers(),
        api.getWorkersHealth(),
        api.getStorageHealth(),
        api.getHealth(),
      ]);
      setUsers(usersRes.data);
      setWorkers(workersRes.data);
      setStorage(storageRes.data);
      setHealth(healthRes.data);
    } catch {
      // silent
    }
  };

  const handleAddUser = async () => {
    if (!newUsername || !newPassword) return;
    try {
      await api.createUser({ username: newUsername, password: newPassword, role: newRole });
      setNewUsername('');
      setNewPassword('');
      setShowAddUser(false);
      loadAll();
    } catch {
      // silent
    }
  };

  const handleToggleUser = async (id: number, isActive: boolean) => {
    await api.toggleUser(id, !isActive);
    loadAll();
  };

  const handleDeleteUser = async (id: number) => {
    await api.deleteUser(id);
    loadAll();
  };

  const formatUptime = (seconds: number): string => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    return `${h}h ${m}m`;
  };

  return (
    <div className="min-h-screen p-6" style={{ background: '#0a0a0a' }}>
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center gap-4 mb-6">
          <button onClick={() => navigate('/')} style={{ color: '#888' }}>
            <ArrowLeft size={20} />
          </button>
          <h1 className="text-lg font-bold tracking-widest" style={{ color: '#00ff88' }}>
            ADMIN PANEL
          </h1>
        </div>

        {/* System Health */}
        <Section title="SYSTEM HEALTH" icon={<Activity size={14} />}>
          <div className="grid grid-cols-3 gap-4">
            <InfoCard label="STATUS" value={health?.status?.toUpperCase() || 'UNKNOWN'} isOk={health?.status === 'ok'} />
            <InfoCard label="UPTIME" value={health ? formatUptime(health.uptime_seconds) : '--'} isOk={true} />
            <InfoCard
              label="STORAGE"
              value={storage ? `${storage.total_size_mb} MB` : '--'}
              isOk={(storage?.total_size_mb ?? 0) < 1000}
            />
          </div>
        </Section>

        {/* Workers */}
        <Section title="WORKERS" icon={<Activity size={14} />}>
          <div className="space-y-2">
            {workers?.workers.map((w) => (
              <div
                key={w.name}
                className="flex items-center justify-between px-3 py-2"
                style={{ background: '#111', border: '1px solid #1a1a1a' }}
              >
                <span className="text-xs tracking-wider" style={{ color: '#e0e0e0' }}>{w.name}</span>
                <div className="flex items-center gap-4">
                  <span
                    className="text-xs px-2 py-0.5"
                    style={{
                      background: w.status === 'running' ? '#0a1a0a' : '#1a0a0a',
                      color: w.status === 'running' ? '#00ff88' : '#ff3333',
                    }}
                  >
                    {w.status.toUpperCase()}
                  </span>
                  <span className="text-xs" style={{ color: '#555' }}>
                    fails: {w.failure_count}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </Section>

        {/* Users */}
        <Section title="USERS" icon={<Users size={14} />}>
          <div className="space-y-2">
            {users.map((u) => (
              <div
                key={u.id}
                className="flex items-center justify-between px-3 py-2"
                style={{ background: '#111', border: '1px solid #1a1a1a' }}
              >
                <div>
                  <span className="text-xs" style={{ color: '#e0e0e0' }}>{u.username}</span>
                  <span className="ml-2 text-xs px-1" style={{ background: '#1a1a2a', color: '#8888ff' }}>
                    {u.role}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleToggleUser(u.id, u.is_active)}
                    style={{ color: u.is_active ? '#00ff88' : '#555' }}
                  >
                    {u.is_active ? <ToggleRight size={16} /> : <ToggleLeft size={16} />}
                  </button>
                  <button onClick={() => handleDeleteUser(u.id)} style={{ color: '#ff3333' }}>
                    <Trash2 size={12} />
                  </button>
                </div>
              </div>
            ))}
          </div>

          {showAddUser ? (
            <div className="mt-3 space-y-2 p-3" style={{ background: '#111', border: '1px solid #1a1a1a' }}>
              <input
                type="text" value={newUsername} onChange={(e) => setNewUsername(e.target.value)}
                placeholder="Username" className="w-full px-2 py-1 text-xs outline-none"
                style={{ background: '#0a0a0a', border: '1px solid #2a2a2a', color: '#e0e0e0' }}
              />
              <input
                type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Password" className="w-full px-2 py-1 text-xs outline-none"
                style={{ background: '#0a0a0a', border: '1px solid #2a2a2a', color: '#e0e0e0' }}
              />
              <select
                value={newRole} onChange={(e) => setNewRole(e.target.value)}
                className="w-full px-2 py-1 text-xs outline-none"
                style={{ background: '#0a0a0a', border: '1px solid #2a2a2a', color: '#e0e0e0' }}
              >
                <option value="client">Client</option>
                <option value="admin">Admin</option>
              </select>
              <button
                onClick={handleAddUser}
                className="w-full py-1 text-xs tracking-wider"
                style={{ background: '#00ff88', color: '#0a0a0a' }}
              >
                CREATE USER
              </button>
            </div>
          ) : (
            <button
              onClick={() => setShowAddUser(true)}
              className="mt-3 flex items-center gap-2 text-xs"
              style={{ color: '#00ff88' }}
            >
              <UserPlus size={14} /> ADD USER
            </button>
          )}
        </Section>

        {/* Storage */}
        <Section title="STORAGE" icon={<HardDrive size={14} />}>
          <div className="grid grid-cols-4 gap-4">
            <InfoCard label="DATABASE" value={`${storage?.db_size_mb ?? 0} MB`} isOk={true} />
            <InfoCard label="FRAMES" value={`${storage?.frames_size_mb ?? 0} MB`} isOk={true} />
            <InfoCard label="COLLAGES" value={`${storage?.collages_size_mb ?? 0} MB`} isOk={true} />
            <InfoCard label="TOTAL" value={`${storage?.total_size_mb ?? 0} MB`} isOk={(storage?.total_size_mb ?? 0) < 1000} />
          </div>
        </Section>
      </div>
    </div>
  );
}

function Section({ title, icon, children }: { title: string; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="mb-6">
      <div className="flex items-center gap-2 mb-3">
        <span style={{ color: '#00ff88' }}>{icon}</span>
        <h2 className="text-xs font-bold tracking-widest" style={{ color: '#888' }}>{title}</h2>
      </div>
      {children}
    </div>
  );
}

function InfoCard({ label, value, isOk }: { label: string; value: string; isOk: boolean }) {
  return (
    <div className="px-3 py-2" style={{ background: '#111', border: '1px solid #1a1a1a' }}>
      <p className="text-xs tracking-wider mb-1" style={{ color: '#555' }}>{label}</p>
      <p className="text-sm font-bold" style={{ color: isOk ? '#e0e0e0' : '#ff3333' }}>{value}</p>
    </div>
  );
}
