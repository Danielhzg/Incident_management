'use client';

import { useState, useEffect, useCallback } from 'react';
import { PostMortem, Incident } from '@/lib/types';
import api from '@/lib/api';

export default function PostMortemView({ incident }: { incident: Incident }) {
  const [postMortem, setPostMortem] = useState<PostMortem | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const isResolvedOrClosed = incident.status === 'resolved' || incident.status === 'closed';

  const fetchPostMortem = useCallback(async () => {
    try {
      const data = await api.getPostMortems(incident.id);
      if (data && data.length > 0) {
        setPostMortem(data[0]);
      }
    } catch (err) {
      console.error('Failed to fetch post-mortem:', err);
    }
  }, [incident.id]);

  useEffect(() => {
    if (isResolvedOrClosed) {
      fetchPostMortem();
    }
  }, [isResolvedOrClosed, fetchPostMortem]);

  const generateAIReport = async () => {
    setLoading(true);
    setError('');
    try {
      const pm = await api.generatePostMortem(incident.id);
      setPostMortem(pm);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to generate post-mortem report.');
    } finally {
      setLoading(false);
    }
  };

  if (!isResolvedOrClosed) {
    return (
      <div className="glass-card p-6 text-center border-amber-500/10">
        <p className="text-sm text-[var(--text-muted)]">
          Post-mortem reports can only be generated once the incident has been resolved or closed.
        </p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="glass-card p-8 flex flex-col items-center justify-center space-y-4 border border-blue-500/20">
        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        <div className="text-center">
          <p className="text-sm font-semibold text-slate-200">Analyzing incident data...</p>
          <p className="text-xs text-[var(--text-muted)] mt-1">Gemini 2.0 Flash is compiling the timeline, root cause, and action items.</p>
        </div>
      </div>
    );
  }

  if (!postMortem) {
    return (
      <div className="glass-card p-8 text-center border-dashed border-[var(--border-color)]">
        <div className="text-3xl mb-3">🧠</div>
        <h4 className="text-sm font-semibold text-slate-200 mb-1">Generate AI Post-Mortem</h4>
        <p className="text-xs text-[var(--text-muted)] max-w-md mx-auto mb-5">
          Leverage Gemini AI to analyze this incident&apos;s chat log, timeline events, and trigger a comprehensive post-mortem draft instantly.
        </p>
        {error && (
          <p className="text-xs text-red-400 bg-red-500/10 border border-red-500/20 p-2.5 rounded-lg mb-4 max-w-md mx-auto">
            {error}
          </p>
        )}
        <button
          onClick={generateAIReport}
          className="px-4 py-2 rounded-lg bg-blue-500/15 hover:bg-blue-500/25 border border-blue-500/30 text-blue-400 font-medium text-xs transition-colors cursor-pointer"
        >
          Generate with Gemini 2.0 Flash
        </button>
      </div>
    );
  }

  return (
    <div className="glass-card p-6 border-slate-800 space-y-6 fade-in">
      <div className="flex items-center justify-between border-b border-[var(--border-color)] pb-4 flex-wrap gap-3">
        <div>
          <h3 className="font-bold text-base text-slate-100">{postMortem.title}</h3>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">
            Generated via AI {postMortem.ai_model ? `(${postMortem.ai_model})` : ''} on{' '}
            {new Date(postMortem.created_at).toLocaleDateString()}
          </p>
        </div>
        <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 font-semibold border border-emerald-500/20">
          AI Draft Ready
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <h4 className="text-xs font-bold uppercase tracking-wider text-[var(--text-secondary)] mb-2 flex items-center gap-1.5">
            📋 Executive Summary
          </h4>
          <p className="text-xs text-slate-300 leading-relaxed bg-[var(--bg-tertiary)] p-3 rounded-lg border border-[var(--border-color)]">
            {postMortem.summary}
          </p>
        </div>

        <div>
          <h4 className="text-xs font-bold uppercase tracking-wider text-[var(--text-secondary)] mb-2 flex items-center gap-1.5">
            🔍 Root Cause
          </h4>
          <p className="text-xs text-slate-300 leading-relaxed bg-[var(--bg-tertiary)] p-3 rounded-lg border border-[var(--border-color)]">
            {postMortem.root_cause}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <h4 className="text-xs font-bold uppercase tracking-wider text-[var(--text-secondary)] mb-2 flex items-center gap-1.5">
            💥 Business & Technical Impact
          </h4>
          <p className="text-xs text-slate-300 leading-relaxed bg-[var(--bg-tertiary)] p-3 rounded-lg border border-[var(--border-color)]">
            {postMortem.impact}
          </p>
        </div>

        <div>
          <h4 className="text-xs font-bold uppercase tracking-wider text-[var(--text-secondary)] mb-2 flex items-center gap-1.5">
            🛠️ Action Items
          </h4>
          <div className="bg-[var(--bg-tertiary)] p-3 rounded-lg border border-[var(--border-color)] text-xs text-slate-300 whitespace-pre-line leading-relaxed">
            {postMortem.action_items}
          </div>
        </div>
      </div>

      <div>
        <h4 className="text-xs font-bold uppercase tracking-wider text-[var(--text-secondary)] mb-2 flex items-center gap-1.5">
          ⏱️ Incident Timeline
        </h4>
        <div className="bg-[var(--bg-tertiary)] p-3 rounded-lg border border-[var(--border-color)] text-xs text-slate-300 whitespace-pre-line leading-relaxed font-mono">
          {postMortem.timeline}
        </div>
      </div>

      {postMortem.lessons_learned && (
        <div>
          <h4 className="text-xs font-bold uppercase tracking-wider text-[var(--text-secondary)] mb-2 flex items-center gap-1.5">
            💡 Lessons Learned
          </h4>
          <p className="text-xs text-slate-300 leading-relaxed bg-[var(--bg-tertiary)] p-3 rounded-lg border border-[var(--border-color)]">
            {postMortem.lessons_learned}
          </p>
        </div>
      )}
    </div>
  );
}
