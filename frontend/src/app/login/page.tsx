'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';

export default function LoginPage() {
  const { login, isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.push('/');
    }
  }, [isAuthenticated, isLoading, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      await login(email, password);
      router.push('/');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Invalid credentials');
    } finally {
      setSubmitting(false);
    }
  };

  const fillCredentials = (userEmail: string) => {
    setEmail(userEmail);
    setPassword('password123');
  };

  if (isLoading || isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--bg-primary)]">
        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--bg-primary)] px-4">
      {/* Background decoration */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-[120px] pointer-events-none" />

      <div className="w-full max-w-md glass-card p-8 relative z-10 fade-in border border-slate-800">
        <div className="text-center mb-8">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold text-lg mx-auto mb-4 shadow-lg shadow-blue-500/20">
            IM
          </div>
          <h2 className="text-2xl font-bold bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
            Incident Manager
          </h2>
          <p className="text-sm text-[var(--text-secondary)] mt-2">
            Sign in to manage active incidents and outages
          </p>
        </div>

        {error && (
          <div className="p-3 mb-6 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)] mb-2">
              Email Address
            </label>
            <input
              type="email"
              required
              placeholder="e.g. alice@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-3 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border-color)] text-white focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/50 transition-all duration-200 text-sm"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)] mb-2">
              Password
            </label>
            <input
              type="password"
              required
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border-color)] text-white focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/50 transition-all duration-200 text-sm"
            />
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full py-3 px-4 rounded-lg bg-gradient-to-r from-blue-500 to-purple-600 text-white font-medium hover:from-blue-600 hover:to-purple-700 transition-all duration-300 shadow-lg shadow-blue-500/20 focus:outline-none disabled:opacity-50 text-sm cursor-pointer"
          >
            {submitting ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <div className="mt-8 border-t border-[var(--border-color)] pt-6">
          <p className="text-xs text-[var(--text-muted)] font-medium uppercase tracking-wider mb-3 text-center">
            Quick demo accounts
          </p>
          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={() => fillCredentials('alice@company.com')}
              className="px-3 py-2 rounded-lg bg-[var(--bg-tertiary)] hover:bg-blue-500/10 border border-[var(--border-color)] text-left hover:border-blue-500/30 transition-all text-xs cursor-pointer"
            >
              <div className="font-semibold text-slate-300">Alice Chen</div>
              <div className="text-[10px] text-[var(--text-muted)]">Engineer (Tier 1)</div>
            </button>
            <button
              onClick={() => fillCredentials('diana@company.com')}
              className="px-3 py-2 rounded-lg bg-[var(--bg-tertiary)] hover:bg-blue-500/10 border border-[var(--border-color)] text-left hover:border-blue-500/30 transition-all text-xs cursor-pointer"
            >
              <div className="font-semibold text-slate-300">Diana Putri</div>
              <div className="text-[10px] text-[var(--text-muted)]">Lead (Tier 2)</div>
            </button>
            <button
              onClick={() => fillCredentials('fiona@company.com')}
              className="px-3 py-2 rounded-lg bg-[var(--bg-tertiary)] hover:bg-blue-500/10 border border-[var(--border-color)] text-left hover:border-blue-500/30 transition-all text-xs cursor-pointer"
            >
              <div className="font-semibold text-slate-300">Fiona Hartono</div>
              <div className="text-[10px] text-[var(--text-muted)]">Manager (Tier 3)</div>
            </button>
            <button
              onClick={() => fillCredentials('bob@company.com')}
              className="px-3 py-2 rounded-lg bg-[var(--bg-tertiary)] hover:bg-blue-500/10 border border-[var(--border-color)] text-left hover:border-blue-500/30 transition-all text-xs cursor-pointer"
            >
              <div className="font-semibold text-slate-300">Bob Raharjo</div>
              <div className="text-[10px] text-[var(--text-muted)]">Engineer (Tier 1)</div>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
