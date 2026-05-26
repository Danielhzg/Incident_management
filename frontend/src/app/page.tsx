'use client';
/**
 * Dashboard — main page with incident metrics overview.
 */
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import Navbar from '@/components/Navbar';
import Sidebar from '@/components/Sidebar';
import IncidentCard from '@/components/IncidentCard';
import api from '@/lib/api';
import { Incident, IncidentStats } from '@/lib/types';

function formatDuration(totalSeconds: number | null | undefined): string {
  if (totalSeconds == null || totalSeconds <= 0) return 'N/A';
  const h = Math.floor(totalSeconds / 3600);
  const m = Math.floor((totalSeconds % 3600) / 60);
  const s = Math.floor(totalSeconds % 60);
  return `${h} jam ${m} menit ${s} detik`;
}

export default function DashboardPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const [stats, setStats] = useState<IncidentStats | null>(null);
  const [recentIncidents, setRecentIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, isLoading, router]);

  useEffect(() => {
    if (isAuthenticated) {
      loadDashboard();
      const interval = setInterval(loadDashboard, 30000);
      return () => clearInterval(interval);
    }
  }, [isAuthenticated]);

  async function loadDashboard() {
    try {
      const [statsData, incidentsData] = await Promise.all([
        api.getStats(),
        api.listIncidents({ per_page: 8 }),
      ]);
      setStats(statsData);
      setRecentIncidents(incidentsData.incidents);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
    } finally {
      setLoading(false);
    }
  }

  if (isLoading || !isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const severityColors: Record<string, string> = {
    P1: 'from-red-500 to-rose-600',
    P2: 'from-orange-500 to-amber-600',
    P3: 'from-yellow-500 to-amber-500',
    P4: 'from-green-500 to-emerald-600',
  };

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <Navbar />
      <Sidebar />

      <main className="pt-20 md:pl-72 px-6 pb-10 max-w-[1600px] mx-auto">
        {/* Header */}
        <div className="mb-8 fade-in">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
            Dashboard
          </h1>
          <p className="text-[var(--text-secondary)] mt-1">
            Real-time incident monitoring and management
          </p>
        </div>

        {loading ? (
          <div className="flex gap-4 overflow-x-auto pb-1 mb-8">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="glass-card p-6 h-32 min-w-[200px] flex-1 shimmer rounded-2xl" />
            ))}
          </div>
        ) : (
          <>
            {/* Stats Cards — 5 cards: Total, Active, Resolved, Closed, MTTR */}
            <div className="flex flex-wrap lg:flex-nowrap gap-4 mb-2">
              {/* Total Incidents */}
              <div className="glass-card p-6 min-w-[180px] flex-1 fade-in hover:border-blue-500/30 transition-all duration-300">
                <p className="text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider">Total Incidents</p>
                <p className="text-3xl font-bold mt-2 bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
                  {stats?.total_incidents || 0}
                </p>
              </div>

              {/* Active */}
              <div className="glass-card p-6 min-w-[180px] flex-1 fade-in hover:border-red-500/30 transition-all duration-300" style={{ animationDelay: '0.1s' }}>
                <p className="text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider">Active</p>
                <p className="text-3xl font-bold mt-2 text-red-400">
                  {(stats?.by_status?.open || 0) + (stats?.by_status?.acknowledged || 0) + (stats?.by_status?.investigating || 0)}
                </p>
                <p className="text-xs text-[var(--text-muted)] mt-3">
                  {stats?.by_status?.open || 0} open · {stats?.by_status?.acknowledged || 0} ack · {stats?.by_status?.investigating || 0} investigating
                </p>
              </div>

              {/* Resolved */}
              <div className="glass-card p-6 min-w-[180px] flex-1 fade-in hover:border-emerald-500/30 transition-all duration-300" style={{ animationDelay: '0.2s' }}>
                <p className="text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider">Resolved</p>
                <p className="text-3xl font-bold mt-2 text-emerald-400">
                  {stats?.by_status?.resolved || 0}
                </p>
                <p className="text-xs text-[var(--text-muted)] mt-3">Fixed, pending formal close</p>
              </div>

              {/* Closed */}
              <div className="glass-card p-6 min-w-[180px] flex-1 fade-in border-slate-500/20 hover:border-slate-400/40 transition-all duration-300" style={{ animationDelay: '0.3s' }}>
                <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Closed</p>
                <p className="text-3xl font-bold mt-2 text-slate-200">
                  {stats?.by_status?.closed ?? 0}
                </p>
                <p className="text-xs text-[var(--text-muted)] mt-3">Archived — no longer active</p>
              </div>

              {/* Avg MTTR */}
              <div className="glass-card p-6 min-w-[180px] flex-1 fade-in hover:border-purple-500/30 transition-all duration-300" style={{ animationDelay: '0.4s' }}>
                <p className="text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider">Avg MTTR</p>
                <p className="text-xl font-bold mt-2 text-purple-400 leading-snug">
                  {formatDuration(stats?.avg_ttr_seconds)}
                </p>
                <p className="text-xs text-[var(--text-muted)] mt-3">Mean Time to Resolution</p>
              </div>
            </div>
            {stats && (
              <p className="text-xs text-[var(--text-muted)] mb-6">
                Total = Active + Resolved + Closed →{' '}
                {stats.total_incidents} ={' '}
                {(stats.by_status?.open || 0) + (stats.by_status?.acknowledged || 0) + (stats.by_status?.investigating || 0)}{' '}
                + {stats.by_status?.resolved || 0} + {stats.by_status?.closed || 0}
              </p>
            )}

            {/* Severity Distribution Bar */}
            {stats && (
              <div className="glass-card p-6 mb-8 fade-in">
                <h2 className="text-sm font-semibold mb-4 text-[var(--text-secondary)]">Severity Distribution</h2>
                <div className="flex gap-3 h-4 rounded-full overflow-hidden bg-[var(--bg-tertiary)]">
                  {['P1', 'P2', 'P3', 'P4'].map(sev => {
                    const count = stats.by_severity?.[sev] || 0;
                    const pct = stats.total_incidents ? (count / stats.total_incidents) * 100 : 0;
                    return pct > 0 ? (
                      <div
                        key={sev}
                        className={`bg-gradient-to-r ${severityColors[sev]} rounded-full transition-all duration-500`}
                        style={{ width: `${pct}%` }}
                        title={`${sev}: ${count} (${pct.toFixed(1)}%)`}
                      />
                    ) : null;
                  })}
                </div>
                <div className="flex gap-6 mt-3">
                  {['P1', 'P2', 'P3', 'P4'].map(sev => (
                    <div key={sev} className="flex items-center gap-2 text-xs text-[var(--text-muted)]">
                      <div className={`w-3 h-3 rounded-full bg-gradient-to-r ${severityColors[sev]}`} />
                      {sev}: {stats.by_severity?.[sev] || 0}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recent Incidents */}
            <div className="fade-in">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-semibold">Recent Incidents</h2>
                <a href="/incidents" className="text-sm text-blue-400 hover:text-blue-300 transition-colors">
                  View all →
                </a>
              </div>
              <div className="grid gap-3">
                {recentIncidents.map(incident => (
                  <IncidentCard key={incident.id} incident={incident} />
                ))}
                {recentIncidents.length === 0 && (
                  <div className="glass-card p-12 text-center text-[var(--text-muted)]">
                    <p>No incidents — everything is running smoothly!</p>
                  </div>
                )}
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
