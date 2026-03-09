import axios from 'axios';

const API_BASE = '/api';

const client = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
});

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('ghost_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('ghost_token');
      localStorage.removeItem('ghost_user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: { id: number; username: string; role: string };
}

export interface UserInfo {
  id: number;
  username: string;
  role: string;
  is_active: boolean;
}

export interface CameraStatus {
  status: string;
  connected_at: string | null;
  last_frame_at: string | null;
  uptime_seconds: number | null;
  buffer_size: number;
  reconnecting: boolean;
}

export interface AlertRule {
  id: number;
  label: string;
  target_text: string;
  is_enabled: boolean;
  days_of_week: string;
  start_time: string;
  end_time: string;
  cooldown_seconds: number;
  last_triggered_at: string | null;
}

export interface AlertEvent {
  id: number;
  rule_id: number;
  match_text: string | null;
  severity: string;
  is_acknowledged: boolean;
  created_at: string;
}

export interface ChatMessage {
  role: string;
  content: string;
  intent: string;
  timestamp: string;
}

export interface MemoryEntry {
  id: number;
  source_type: string;
  timestamp_start: string;
  timestamp_end: string;
  text_summary: string;
  people_count: number;
  vehicle_count: number;
  motion_level: string | null;
  created_at: string;
}

export interface HealthInfo {
  status: string;
  uptime_seconds: number;
  timestamp: string;
}

export interface WorkersHealth {
  workers: Array<{
    name: string;
    status: string;
    last_heartbeat: string | null;
    failure_count: number;
    last_error: string | null;
  }>;
}

export interface StorageHealth {
  db_size_mb: number;
  frames_size_mb: number;
  collages_size_mb: number;
  total_size_mb: number;
}

export const api = {
  login: (username: string, password: string) =>
    client.post<LoginResponse>('/auth/login', { username, password }),

  getMe: () => client.get<UserInfo>('/auth/me'),
  logout: () => client.post('/auth/logout'),

  getCameraStatus: () => client.get<CameraStatus>('/camera/status'),
  reconnectCamera: () => client.post('/camera/reconnect'),

  getAlertRules: () => client.get<AlertRule[]>('/alerts/rules'),
  createAlertRule: (data: Omit<AlertRule, 'id' | 'is_enabled' | 'last_triggered_at'>) =>
    client.post<AlertRule>('/alerts/rules', data),
  updateAlertRule: (id: number, data: Partial<AlertRule>) =>
    client.patch<AlertRule>(`/alerts/rules/${id}`, data),
  deleteAlertRule: (id: number) => client.delete(`/alerts/rules/${id}`),
  getAlertEvents: (limit?: number) =>
    client.get<AlertEvent[]>('/alerts/events', { params: { limit: limit || 20 } }),

  sendChat: (message: string) =>
    client.post<ChatMessage>('/chat/message', { message }),
  getChatHistory: (limit?: number) =>
    client.get<ChatMessage[]>('/chat/history', { params: { limit: limit || 50 } }),

  getMemory: (params?: { from?: string; to?: string; query?: string; objects?: string }) =>
    client.get<MemoryEntry[]>('/history/memory', { params }),
  getTimeline: (limit?: number) =>
    client.get<MemoryEntry[]>('/history/timeline', { params: { limit } }),

  getHealth: () => client.get<HealthInfo>('/health'),
  getWorkersHealth: () => client.get<WorkersHealth>('/health/workers'),
  getStorageHealth: () => client.get<StorageHealth>('/health/storage'),

  getUsers: () => client.get<UserInfo[]>('/admin/users'),
  createUser: (data: { username: string; password: string; role: string }) =>
    client.post('/admin/users', data),
  toggleUser: (id: number, is_active: boolean) =>
    client.patch(`/admin/users/${id}`, { is_active }),
  deleteUser: (id: number) => client.delete(`/admin/users/${id}`),
  resetPassword: (id: number, new_password: string) =>
    client.post(`/admin/users/${id}/reset-password`, { new_password }),
};

export default api;
