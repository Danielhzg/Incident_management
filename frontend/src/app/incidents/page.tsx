'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import Navbar from '@/components/Navbar';
import Sidebar from '@/components/Sidebar';
import IncidentCard from '@/components/IncidentCard';
import api from '@/lib/api';
import { Incident, IncidentSeverity, IncidentStatus } from '@/lib/types';

export default function IncidentsPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  // Filter and search states
  const [search, setSearch] = useState('');
  const [severity, setSeverity] = useState<IncidentSeverity | ''>('');
  const [status, setStatus] = useState<IncidentStatus | ''>('');
  const [page, setPage] = useState(1);
  const [perPage] = useState(10);

  // Data states
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  // Create Incident Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [newSev, setNewSev] = useState<IncidentSeverity>('P3');
  const [newTags, setNewTags] = useState('');
  const [newSource, setNewSource] = useState('manual');
  const [createError, setCreateError] = useState('');
  const [creating, setCreating] = useState(false);

  const fetchIncidents = useCallback(async () => {
    setLoading(true);
    try {
      const response = await api.listIncidents({
        page,
        per_page: perPage,
        severity: severity || undefined,
        status: status || undefined,
        search: search || undefined,
      });
      setIncidents(response.incidents);
      setTotal(response.total);
    } catch (err) {
      console.error('Failed to fetch incidents:', err);
    } finally {
      setLoading(false);
    }
  }, [page, perPage, severity, status, search]);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, isLoading, router]);

  useEffect(() => {
    if (isAuthenticated) {
      fetchIncidents();
    }
  }, [isAuthenticated, fetchIncidents]);

  const handleCreateIncident = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateError('');
    setCreating(true);
    try {
      await api.createIncident({
        title: newTitle,
        description: newDesc,
        severity: newSev,
        source: newSource,
        tags: newTags,
      });
      setIsModalOpen(false);
      // Reset form
      setNewTitle('');
      setNewDesc('');
      setNewSev('P3');
      setNewTags('');
      setNewSource('manual');
      // Refetch
      fetchIncidents();
    } catch (err: unknown) {
      setCreateError(err instanceof Error ? err.message : 'Failed to create incident');
    } finally {
      setCreating(false);
    }
  };

  if (isLoading || !isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--bg-primary)]">
        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const totalPages = Math.ceil(total / perPage);

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <Navbar />
      <Sidebar />

      <main className="pt-20 md:pl-72 px-6 pb-10 max-w-[1600px] mx-auto">
        {/* Header section */}
        <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 mb-8 fade-in">
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
              Incidents
            </h1>
            <p className="text-[var(--text-secondary)] mt-1">
              Showing {incidents.length} of {total} total incidents
            </p>
          </div>
          <button
            onClick={() => setIsModalOpen(true)}
            className="self-start sm:self-auto px-4 py-2.5 rounded-xl bg-blue-500 hover:bg-blue-600 text-white font-medium text-sm transition-all duration-300 shadow-lg shadow-blue-500/20 cursor-pointer"
          >
            + Create Incident
          </button>
        </div>

        {/* Filter Toolbar */}
        <div className="glass-card p-4 mb-6 grid grid-cols-1 sm:grid-cols-3 gap-4 fade-in">
          <div>
            <label className="block text-[10px] font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1.5">
              Search Title / Tags
            </label>
            <input
              type="text"
              placeholder="Type to search..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              className="w-full px-3 py-2 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border-color)] text-white focus:outline-none focus:border-blue-500/50 text-xs transition-colors"
            />
          </div>

          <div>
            <label className="block text-[10px] font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1.5">
              Filter by Severity
            </label>
            <select
              value={severity}
              onChange={(e) => {
                setSeverity(e.target.value as IncidentSeverity | '');
                setPage(1);
              }}
              className="w-full px-3 py-2 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border-color)] text-white focus:outline-none focus:border-blue-500/50 text-xs transition-colors cursor-pointer"
            >
              <option value="">All Severities</option>
              <option value="P1">P1 Critical</option>
              <option value="P2">P2 High</option>
              <option value="P3">P3 Medium</option>
              <option value="P4">P4 Low</option>
            </select>
          </div>

          <div>
            <label className="block text-[10px] font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-1.5">
              Filter by Status
            </label>
            <select
              value={status}
              onChange={(e) => {
                setStatus(e.target.value as IncidentStatus | '');
                setPage(1);
              }}
              className="w-full px-3 py-2 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border-color)] text-white focus:outline-none focus:border-blue-500/50 text-xs transition-colors cursor-pointer"
            >
              <option value="">All Statuses</option>
              <option value="open">Open</option>
              <option value="acknowledged">Acknowledged</option>
              <option value="investigating">Investigating</option>
              <option value="resolved">Resolved</option>
              <option value="closed">Closed</option>
            </select>
          </div>
        </div>

        {/* Incidents List */}
        {loading ? (
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="glass-card p-5 h-28 shimmer rounded-xl" />
            ))}
          </div>
        ) : (
          <div className="space-y-3">
            {incidents.map((incident) => (
              <IncidentCard key={incident.id} incident={incident} />
            ))}

            {incidents.length === 0 && (
              <div className="glass-card p-16 text-center text-[var(--text-muted)]">
                <p className="text-4xl mb-3">🔍</p>
                <p className="font-medium text-slate-300">No matching incidents found</p>
                <p className="text-xs mt-1">Try adjusting your filters or search query.</p>
              </div>
            )}

            {/* Pagination Controls */}
            {totalPages > 1 && (
              <div className="flex justify-between items-center mt-6 pt-4 border-t border-[var(--border-color)]">
                <button
                  disabled={page === 1}
                  onClick={() => setPage((p) => p - 1)}
                  className="px-3 py-1.5 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border-color)] hover:bg-[var(--bg-secondary)] disabled:opacity-40 transition-colors text-xs font-semibold cursor-pointer text-slate-300"
                >
                  ← Previous
                </button>
                <span className="text-xs text-[var(--text-muted)]">
                  Page {page} of {totalPages}
                </span>
                <button
                  disabled={page === totalPages}
                  onClick={() => setPage((p) => p + 1)}
                  className="px-3 py-1.5 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border-color)] hover:bg-[var(--bg-secondary)] disabled:opacity-40 transition-colors text-xs font-semibold cursor-pointer text-slate-300"
                >
                  Next →
                </button>
              </div>
            )}
          </div>
        )}
      </main>

      {/* Create Incident Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm transition-all duration-300">
          <div className="w-full max-w-lg glass-card border border-slate-800 p-6 relative slide-in">
            <button
              onClick={() => setIsModalOpen(false)}
              className="absolute right-4 top-4 p-1.5 text-[var(--text-muted)] hover:text-white rounded-lg hover:bg-[var(--bg-tertiary)] transition-colors cursor-pointer"
            >
              ✕
            </button>
            <h2 className="text-xl font-bold mb-4 bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
              Create New Incident
            </h2>

            {createError && (
              <div className="p-3 mb-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs">
                {createError}
              </div>
            )}

            <form onSubmit={handleCreateIncident} className="space-y-4">
              <div>
                <label className="block text-[10px] font-semibold uppercase tracking-wider text-[var(--text-secondary)] mb-1.5">
                  Incident Title
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Memory leak in order service"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border-color)] text-white focus:outline-none focus:border-blue-500/50 text-xs transition-colors"
                />
              </div>

              <div>
                <label className="block text-[10px] font-semibold uppercase tracking-wider text-[var(--text-secondary)] mb-1.5">
                  Severity
                </label>
                <div className="grid grid-cols-4 gap-2">
                  {(['P1', 'P2', 'P3', 'P4'] as IncidentSeverity[]).map((sev) => {
                    const colors = {
                      P1: 'border-red-500/30 text-red-400 hover:bg-red-500/10',
                      P2: 'border-orange-500/30 text-orange-400 hover:bg-orange-500/10',
                      P3: 'border-yellow-500/30 text-yellow-400 hover:bg-yellow-500/10',
                      P4: 'border-green-500/30 text-green-400 hover:bg-green-500/10',
                    };
                    const activeColors = {
                      P1: 'bg-red-500/20 border-red-500',
                      P2: 'bg-orange-500/20 border-orange-500',
                      P3: 'bg-yellow-500/20 border-yellow-500',
                      P4: 'bg-green-500/20 border-green-500',
                    };
                    return (
                      <button
                        key={sev}
                        type="button"
                        onClick={() => setNewSev(sev)}
                        className={`py-2 rounded-lg border text-center font-bold text-xs transition-all cursor-pointer ${
                          newSev === sev ? activeColors[sev] : colors[sev]
                        }`}
                      >
                        {sev}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div>
                <label className="block text-[10px] font-semibold uppercase tracking-wider text-[var(--text-secondary)] mb-1.5">
                  Description
                </label>
                <textarea
                  required
                  rows={4}
                  placeholder="Detail the metrics, symptoms, and potential impact..."
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border-color)] text-white focus:outline-none focus:border-blue-500/50 text-xs transition-colors resize-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-[10px] font-semibold uppercase tracking-wider text-[var(--text-secondary)] mb-1.5">
                    Source
                  </label>
                  <select
                    value={newSource}
                    onChange={(e) => setNewSource(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border-color)] text-white focus:outline-none focus:border-blue-500/50 text-xs transition-colors cursor-pointer"
                  >
                    <option value="manual">Manual Reporting</option>
                    <option value="monitoring">Monitoring Alert</option>
                    <option value="webhook">Partner Webhook</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[10px] font-semibold uppercase tracking-wider text-[var(--text-secondary)] mb-1.5">
                    Tags (Comma Separated)
                  </label>
                  <input
                    type="text"
                    placeholder="database, checkout, api"
                    value={newTags}
                    onChange={(e) => setNewTags(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border-color)] text-white focus:outline-none focus:border-blue-500/50 text-xs transition-colors"
                  />
                </div>
              </div>

              <div className="flex gap-3 justify-end pt-4 border-t border-[var(--border-color)]">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-lg bg-[var(--bg-tertiary)] hover:bg-[var(--bg-secondary)] border border-[var(--border-color)] text-xs text-slate-300 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="px-4 py-2 rounded-lg bg-blue-500 hover:bg-blue-600 text-white font-semibold text-xs disabled:opacity-50 cursor-pointer"
                >
                  {creating ? 'Creating...' : 'Create Incident'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
