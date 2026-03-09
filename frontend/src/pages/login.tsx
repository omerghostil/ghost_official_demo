import { useState, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { Eye, EyeOff, Shield } from 'lucide-react';
import api from '../api/client';
import { useAuthStore } from '../store/auth-store';

export function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const login = useAuthStore((s) => s.login);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const { data } = await api.login(username, password);
      login(data.access_token, data.user);
      navigate('/');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center" style={{ background: '#0a0a0a' }}>
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <Shield size={48} strokeWidth={1} style={{ color: '#00ff88' }} />
          </div>
          <h1 className="text-2xl font-bold tracking-wider" style={{ color: '#e0e0e0' }}>
            GHOST BRAIN
          </h1>
          <p className="text-xs mt-1 tracking-widest uppercase" style={{ color: '#555' }}>
            Surveillance Memory System
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="USERNAME"
              autoComplete="username"
              className="w-full px-4 py-3 text-sm tracking-wider outline-none"
              style={{
                background: '#111',
                border: '1px solid #2a2a2a',
                color: '#e0e0e0',
              }}
            />
          </div>

          <div className="relative">
            <input
              type={showPassword ? 'text' : 'password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="PASSWORD"
              autoComplete="current-password"
              className="w-full px-4 py-3 text-sm tracking-wider outline-none pr-10"
              style={{
                background: '#111',
                border: '1px solid #2a2a2a',
                color: '#e0e0e0',
              }}
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2"
              style={{ color: '#555' }}
            >
              {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>

          {error && (
            <div className="text-xs py-2 px-3" style={{ color: '#ff3333', background: '#1a0000', border: '1px solid #330000' }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading || !username || !password}
            className="w-full py-3 text-sm font-bold tracking-widest uppercase transition-all"
            style={{
              background: isLoading ? '#1a1a1a' : '#00ff88',
              color: '#0a0a0a',
              opacity: isLoading || !username || !password ? 0.5 : 1,
              cursor: isLoading ? 'wait' : 'pointer',
            }}
          >
            {isLoading ? 'CONNECTING...' : 'ACCESS SYSTEM'}
          </button>
        </form>

        <p className="text-center mt-6 text-xs" style={{ color: '#333' }}>
          LOCAL SYSTEM v1.0
        </p>
      </div>
    </div>
  );
}
