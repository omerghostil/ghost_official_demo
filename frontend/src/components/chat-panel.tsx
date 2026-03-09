import { useState, useEffect, useRef, FormEvent } from 'react';
import { Send, MessageCircle } from 'lucide-react';
import type { ChatMessage } from '../api/client';
import api from '../api/client';

export function ChatPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadHistory();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadHistory = async () => {
    try {
      const { data } = await api.getChatHistory(30);
      setMessages(data);
    } catch {
      // silent
    }
  };

  const handleSend = async (e: FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMsg: ChatMessage = {
      role: 'user',
      content: input,
      intent: '',
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      const { data } = await api.sendChat(input);
      setMessages((prev) => [...prev, data]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Connection error', intent: 'error', timestamp: '' },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full" style={{ background: '#111', borderLeft: '1px solid #1a1a1a' }}>
      <div className="flex items-center gap-2 px-3 py-2" style={{ borderBottom: '1px solid #1a1a1a' }}>
        <MessageCircle size={14} style={{ color: '#00ff88' }} />
        <span className="text-xs tracking-wider" style={{ color: '#888' }}>GHOST CHAT</span>
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-3" style={{ maxHeight: 'calc(100vh - 200px)' }}>
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className="max-w-[85%] px-3 py-2 text-xs leading-relaxed"
              style={{
                background: msg.role === 'user' ? '#1a2a1a' : '#1a1a1a',
                border: `1px solid ${msg.role === 'user' ? '#2a3a2a' : '#2a2a2a'}`,
                color: '#e0e0e0',
              }}
            >
              <p style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</p>
              {msg.timestamp && (
                <p className="mt-1" style={{ color: '#444', fontSize: '10px' }}>
                  {new Date(msg.timestamp).toLocaleTimeString()}
                </p>
              )}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="px-3 py-2 text-xs" style={{ color: '#555' }}>
              analyzing...
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSend} className="flex gap-2 p-3" style={{ borderTop: '1px solid #1a1a1a' }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask Ghost Brain..."
          className="flex-1 px-3 py-2 text-xs outline-none"
          style={{ background: '#0a0a0a', border: '1px solid #2a2a2a', color: '#e0e0e0' }}
        />
        <button
          type="submit"
          disabled={!input.trim() || isLoading}
          className="px-3 py-2"
          style={{
            background: input.trim() ? '#00ff88' : '#1a1a1a',
            color: '#0a0a0a',
            opacity: !input.trim() || isLoading ? 0.3 : 1,
          }}
        >
          <Send size={14} />
        </button>
      </form>
    </div>
  );
}
