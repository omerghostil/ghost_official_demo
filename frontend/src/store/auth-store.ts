import { create } from 'zustand';

interface AuthUser {
  id: number;
  username: string;
  role: string;
}

interface AuthState {
  token: string | null;
  user: AuthUser | null;
  isAuthenticated: boolean;
  login: (token: string, user: AuthUser) => void;
  logout: () => void;
  hydrate: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  user: null,
  isAuthenticated: false,

  login: (token, user) => {
    localStorage.setItem('ghost_token', token);
    localStorage.setItem('ghost_user', JSON.stringify(user));
    set({ token, user, isAuthenticated: true });
  },

  logout: () => {
    localStorage.removeItem('ghost_token');
    localStorage.removeItem('ghost_user');
    set({ token: null, user: null, isAuthenticated: false });
  },

  hydrate: () => {
    const token = localStorage.getItem('ghost_token');
    const userStr = localStorage.getItem('ghost_user');
    if (token && userStr) {
      try {
        const user = JSON.parse(userStr);
        set({ token, user, isAuthenticated: true });
      } catch {
        set({ token: null, user: null, isAuthenticated: false });
      }
    }
  },
}));
