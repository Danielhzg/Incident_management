'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import Navbar from '@/components/Navbar';
import Sidebar from '@/components/Sidebar';
import StatusBadge, { SeverityBadge } from '@/components/StatusBadge';
import Timeline from '@/components/Timeline';
import PostMortemView from '@/components/PostMortemView';
import api from '@/lib/api';
import { Incident } from '@/lib/types';

export default function IncidentDetailPage({ params }: { params: { id: string } }) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const incidentId = parseInt(params.id);

  const [incident, setIncident] = useState<Incident | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [resolutionNotes, setResolutionNotes] = useState('');

  const loadIncident = useCallback(async () => {
    try {
      const data = await api.getIncident(incidentId);
      setIncident(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to fetch incident details');
    } finally {
      setLoading(false);
    }
  }, [incidentId]);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, isLoading, router]);

  useEffect(() => {
    if (isAuthenticated && incidentId) {
      loadIncident();
      // Auto-refresh detail page every 15 seconds to sync state machine & notifications
      const interval = setInterval(loadIncident, 15000);
      return () => clearInterval(interval);
    }
  }, [isAuthenticated, incidentId, loadIncident]);

  const handleAcknowledge = async () => {
    setActionLoading(true);
    setError('');
    try {
      await api.acknowledgeIncident(incidentId);
      await loadIncident();
    } catch (err: unknown) {
      // Race condition (409 Conflict) or general error
      setError(err instanceof Error ? err.message : 'Failed to acknowledge incident');
    } finally {
      setActionLoading(false);
    }
  };

  const handleResolve = async () => {
    if (!resolutionNotes.trim()) {
      setError('Please provide resolution notes detailing the fix.');
      return;
    }
    setActionLoading(true);
    setError('');
    try {
      await api.resolveIncident(incidentId, resolutionNotes);
      setResolutionNotes('');
      await loadIncident();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to resolve incident');
    } finally {
      setActionLoading(false);
    }
  };

  const handleClose = async () => {
    setActionLoading(true);
    setError('');
    try {
      await api.closeIncident(incidentId);
      await loadIncident();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to close incident');
    } finally {
      setActionLoading(false);
    }
  };

  if (isLoading || !isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--bg-primary)]">
        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-[var(--bg-primary)]">
        <Navbar />
        <Sidebar />
        <main className="pt-20 md:pl-72 px-6 pb-10 max-w-[1600px] mx-auto flex items-center justify-center h-[70vh]">
          <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        </main>
      </div>
    );
  }

  if (!incident) {
    return (
      <div className="min-h-screen bg-[var(--bg-primary)]">
        <Navbar />
        <Sidebar />
        <main className="pt-20 md:pl-72 px-6 pb-10 max-w-[1600px] mx-auto text-center mt-20">
          <h2 className="text-xl font-bold text-red-400">Incident Not Found</h2>
          <p className="text-sm text-[var(--text-muted)] mt-2">The incident you are trying to view does not exist or has been deleted.</p>
          <button
            onClick={() => router.push('/incidents')}
            className="mt-6 px-4 py-2 bg-blue-500 text-white text-xs font-semibold rounded-lg hover:bg-blue-600 transition-colors"
          >
            Back to Incidents
          </button>
        </main>
      </div>
    );
  }

  const isResolved = incident.status === 'resolved';
  const isClosed = incident.status === 'closed';

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <Navbar />
      <Sidebar />

      <main className="pt-20 md:pl-72 px-6 pb-10 max-w-[1600px] mx-auto">
        {/* Navigation Breadcrumb */}
        <div className="mb-4">
          <button
            onClick={() => router.push('/incidents')}
            className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1.5 cursor-pointer"
          >
            ← Back to Incidents list
          </button>
        </div>

        {/* Incident Summary Card */}
        <div className="glass-card p-6 mb-6 border-slate-800 fade-in">
          <div className="flex flex-col md:flex-row justify-between items-start gap-4">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-3 flex-wrap">
                <SeverityBadge severity={incident.severity} />
                <StatusBadge status={incident.status} />
                {incident.escalation_count > 0 && (
                  <span className="text-xs px-2.5 py-0.5 rounded-full bg-purple-500/20 text-purple-400 font-medium border border-purple-500/10">
                    ⬆ Escalated ×{incident.escalation_count} (Tier {incident.escalation_tier})
                  </span>
                )}
              </div>
              <h1 className="text-2xl font-bold text-slate-100">
                #{incident.id} — {incident.title}
              </h1>
              <p className="text-xs text-[var(--text-muted)] mt-1.5">
                Reported {new Date(incident.created_at).toLocaleString()} via{' '}
                <span className="font-semibold text-slate-400 capitalize">{incident.source}</span>
              </p>
            </div>
          </div>

          <div className="mt-6 pt-6 border-t border-[var(--border-color)]">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-2">
              Description
            </h3>
            <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-line bg-[var(--bg-tertiary)] p-4 rounded-xl border border-[var(--border-color)]">
              {incident.description}
            </p>
          </div>
        </div>

        {/* Dynamic Action Center & Timeline Panels */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* Main Action / Detail Panel (Left) */}
          <div className="lg:col-span-2 space-y-6">
            {/* Incident Actions Panel */}
            <div className="glass-card p-6 border-slate-800 fade-in">
              <h2 className="text-sm font-bold uppercase tracking-wider text-[var(--text-secondary)] mb-4">
                🛠️ Incident Responder Panel
              </h2>

              {error && (
                <div className="p-3 mb-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs">
                  {error}
                </div>
              )}

              {/* Status workflow */}
              {incident.status === 'open' && (
                <div className="space-y-4">
                  <div className="p-3.5 rounded-xl bg-blue-500/5 border border-blue-500/10 text-xs text-blue-400">
                    <strong>Locking Mechanism (SET NX) Active:</strong> Acknowledging this incident will reserve it in Redis to prevent concurrent responder conflicts.
                  </div>
                  <button
                    onClick={handleAcknowledge}
                    disabled={actionLoading}
                    className="px-5 py-2.5 rounded-xl bg-blue-500 hover:bg-blue-600 text-white font-semibold text-xs transition-all shadow-md shadow-blue-500/10 cursor-pointer disabled:opacity-50"
                  >
                    {actionLoading ? 'Aclaiming Lock...' : 'Acknowledge Incident'}
                  </button>
                </div>
              )}

              {(incident.status === 'acknowledged' || incident.status === 'investigating') && (
                <div className="space-y-4">
                  <div>
                    <label className="block text-[10px] font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-2">
                      Resolution Notes (Required)
                    </label>
                    <textarea
                      rows={3}
                      placeholder="Detail the root cause and the fix applied..."
                      value={resolutionNotes}
                      onChange={(e) => setResolutionNotes(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border-color)] text-white focus:outline-none focus:border-blue-500/50 text-xs transition-colors resize-none"
                    />
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={handleResolve}
                      disabled={actionLoading}
                      className="px-5 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white font-semibold text-xs transition-all shadow-md shadow-emerald-500/10 cursor-pointer disabled:opacity-50"
                    >
                      {actionLoading ? 'Resolving...' : 'Resolve Incident'}
                    </button>
                  </div>
                </div>
              )}

              {isResolved && (
                <div className="space-y-4">
                  <div className="p-4 rounded-xl bg-emerald-500/5 border border-emerald-500/10 text-xs text-emerald-400 font-semibold flex items-center gap-2">
                    <span>✅</span> Incident resolved — SLA timers cleared. Close when post-mortem is complete.
                  </div>
                  <button
                    onClick={handleClose}
                    disabled={actionLoading}
                    className="px-5 py-2.5 rounded-xl bg-slate-600 hover:bg-slate-500 text-white font-semibold text-xs transition-all shadow-md cursor-pointer disabled:opacity-50"
                  >
                    {actionLoading ? 'Closing...' : 'Close Incident (Archive)'}
                  </button>
                </div>
              )}

              {isClosed && (
                <div className="p-4 rounded-xl bg-slate-500/10 border border-slate-500/20 text-xs text-slate-300 font-semibold flex items-center gap-2">
                  <span>📁</span> This incident is closed and archived. No further actions required.
                </div>
              )}
            </div>

            {/* AI Post-Mortem Card */}
            <div className="fade-in">
              <h2 className="text-sm font-bold uppercase tracking-wider text-[var(--text-secondary)] mb-3">
                🧠 AI-Powered Post-Mortem Report
              </h2>
              <PostMortemView incident={incident} />
            </div>
          </div>

          {/* Incident Metadata & Timeline Sidebar (Right) */}
          <div className="space-y-6">
            {/* Metadata Card */}
            <div className="glass-card p-6 border-slate-800 fade-in" style={{ animationDelay: '0.1s' }}>
              <h2 className="text-sm font-bold uppercase tracking-wider text-[var(--text-secondary)] mb-4">
                ℹ️ Metadata
              </h2>
              <div className="space-y-3.5 text-xs">
                <div className="flex justify-between items-center pb-2 border-b border-[var(--border-color)]">
                  <span className="text-[var(--text-muted)]">Source</span>
                  <span className="font-semibold text-slate-300 capitalize">{incident.source}</span>
                </div>
                <div className="flex justify-between items-center pb-2 border-b border-[var(--border-color)]">
                  <span className="text-[var(--text-muted)]">Current Tier</span>
                  <span className="font-semibold text-slate-300">Tier {incident.escalation_tier}</span>
                </div>
                <div className="flex justify-between items-center pb-2 border-b border-[var(--border-color)]">
                  <span className="text-[var(--text-muted)]">Assignee</span>
                  <span className="font-semibold text-slate-300">{incident.assignee_name || 'Unassigned'}</span>
                </div>
                <div className="flex justify-between items-center pb-2 border-b border-[var(--border-color)]">
                  <span className="text-[var(--text-muted)]">Acknowledged By</span>
                  <span className="font-semibold text-slate-300">{incident.acknowledger_name || 'N/A'}</span>
                </div>
                {incident.resolved_by && (
                  <div className="flex justify-between items-center pb-2 border-b border-[var(--border-color)]">
                    <span className="text-[var(--text-muted)]">Resolved By</span>
                    <span className="font-semibold text-slate-300">{incident.resolver_name || 'N/A'}</span>
                  </div>
                )}
                {incident.tags && (
                  <div>
                    <span className="text-[var(--text-muted)] block mb-1.5">Tags</span>
                    <div className="flex gap-1 flex-wrap">
                      {incident.tags.split(',').map(tag => (
                        <span key={tag} className="text-[10px] px-2 py-0.5 rounded bg-[var(--bg-tertiary)] border border-[var(--border-color)] text-slate-400">
                          {tag.trim()}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Timeline Events Card */}
            <div className="glass-card p-6 border-slate-800 fade-in" style={{ animationDelay: '0.2s' }}>
              <h2 className="text-sm font-bold uppercase tracking-wider text-[var(--text-secondary)] mb-4">
                ⏱️ Chronological Timeline
              </h2>
              <Timeline incident={incident} />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
