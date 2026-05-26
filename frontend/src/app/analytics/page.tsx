'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import Navbar from '@/components/Navbar';
import Sidebar from '@/components/Sidebar';
import { AvgMttrChart, HourlyDistributionChart, TopTagsCloud } from '@/components/AnalyticsChart';
import api from '@/lib/api';
import { ClusterData, InsightsData } from '@/lib/types';

export default function AnalyticsPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  const [clusters, setClusters] = useState<ClusterData | null>(null);
  const [insightsData, setInsightsData] = useState<InsightsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, isLoading, router]);

  useEffect(() => {
    if (isAuthenticated) {
      loadAnalyticsData();
    }
  }, [isAuthenticated]);

  const loadAnalyticsData = async () => {
    setLoading(true);
    try {
      const [clusterRes, insightsRes] = await Promise.all([
        api.getClusters(),
        api.getInsights(),
      ]);
      setClusters(clusterRes);
      setInsightsData(insightsRes);
    } catch (err) {
      console.error('Failed to load analytics datasets:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      const [clusterRes, insightsRes] = await Promise.all([
        api.getClusters(),
        api.getInsights(),
      ]);
      setClusters(clusterRes);
      setInsightsData(insightsRes);
    } catch (err) {
      console.error('Failed to refresh analytics datasets:', err);
    } finally {
      setRefreshing(false);
    }
  };

  if (isLoading || !isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--bg-primary)]">
        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <Navbar />
      <Sidebar />

      <main className="pt-20 md:pl-72 px-6 pb-10 max-w-[1600px] mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8 fade-in">
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
              AI Analytics & Insights
            </h1>
            <p className="text-[var(--text-secondary)] mt-1">
              Deep cluster analysis and predictive recommendations powered by Gemini 2.0 Flash
            </p>
          </div>
          <button
            onClick={handleRefresh}
            disabled={loading || refreshing}
            className="px-4 py-2 rounded-xl bg-[var(--bg-tertiary)] hover:bg-[var(--bg-secondary)] border border-[var(--border-color)] text-slate-300 font-semibold text-xs transition-all cursor-pointer flex items-center gap-1.5 disabled:opacity-40"
          >
            {refreshing ? 'Analyzing...' : 'Re-Analyze'}
          </button>
        </div>

        {loading ? (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="glass-card p-6 h-36 shimmer rounded-xl" />
              ))}
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 glass-card p-6 h-64 shimmer rounded-xl" />
              <div className="glass-card p-6 h-64 shimmer rounded-xl" />
            </div>
          </div>
        ) : (
          <div className="space-y-8">
            {/* Overview Mini Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 fade-in">
              <div className="glass-card p-5 border-slate-800">
                <p className="text-[10px] font-semibold text-[var(--text-muted)] uppercase tracking-wider">Analyzed Scope</p>
                <p className="text-2xl font-bold text-slate-100 mt-1">{clusters?.total_analyzed || 0} Incidents</p>
              </div>

              <div className="glass-card p-5 border-slate-800">
                <p className="text-[10px] font-semibold text-[var(--text-muted)] uppercase tracking-wider">Peak Incident Hour</p>
                <p className="text-2xl font-bold text-slate-100 mt-1">
                  {clusters?.peak_hour !== null && clusters?.peak_hour !== undefined
                    ? `${String(clusters.peak_hour).padStart(2, '0')}:00 - ${String((clusters.peak_hour + 1) % 24).padStart(2, '0')}:00`
                    : 'N/A'}
                </p>
              </div>

              <div className="glass-card p-5 border-slate-800">
                <p className="text-[10px] font-semibold text-[var(--text-muted)] uppercase tracking-wider">AI Accuracy Model</p>
                <p className="text-2xl font-bold text-slate-100 mt-1">Gemini 2.0 Flash</p>
              </div>
            </div>

            {/* AI Insights & Predictions Panel */}
            <div className="glass-card p-6 border-slate-800 border-l-4 border-l-purple-500 fade-in" style={{ animationDelay: '0.1s' }}>
              <h2 className="text-base font-bold text-slate-200 mb-2">Gemini Strategic Recommendations</h2>
              <p className="text-xs text-[var(--text-muted)] mb-5">
                Predictive analytics and structural optimizations based on incident clusters:
              </p>

              <div className="space-y-4">
                {insightsData && Array.isArray(insightsData.insights) ? (
                  insightsData.insights.map((item, idx) => {
                    const colorMap: Record<string, { bg: string; text: string; border: string }> = {
                      critical: { bg: 'bg-red-500/10', text: 'text-red-400', border: 'border-red-500/20' },
                      high: { bg: 'bg-orange-500/10', text: 'text-orange-400', border: 'border-orange-500/20' },
                      medium: { bg: 'bg-yellow-500/10', text: 'text-yellow-400', border: 'border-yellow-500/20' },
                      low: { bg: 'bg-green-500/10', text: 'text-green-400', border: 'border-green-500/20' },
                    };
                    const type = item.severity?.toLowerCase() || 'medium';
                    const styles = colorMap[type] || colorMap.medium;

                    return (
                      <div
                        key={idx}
                        className={`p-4 rounded-xl border ${styles.bg} ${styles.border} space-y-2`}
                      >
                        <div className="flex justify-between items-start gap-4">
                          <h4 className="text-sm font-bold text-slate-100">{item.insight}</h4>
                          <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${styles.text} border ${styles.border}`}>
                            {item.severity}
                          </span>
                        </div>
                        <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
                          <strong>Action Plan:</strong> {item.recommendation}
                        </p>
                      </div>
                    );
                  })
                ) : insightsData && typeof insightsData.insights === 'string' ? (
                  <div className="p-4 rounded-xl bg-[var(--bg-tertiary)] text-xs text-slate-300 leading-relaxed whitespace-pre-line">
                    {insightsData.insights}
                  </div>
                ) : (
                  <div className="p-8 text-center text-xs text-[var(--text-muted)]">
                    Could not parse AI insights summary. Check backend configuration or API Key limits.
                  </div>
                )}
              </div>
            </div>

            {/* Visual Analytics Charts Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 fade-in" style={{ animationDelay: '0.2s' }}>
              <div className="lg:col-span-2">
                <HourlyDistributionChart
                  data={clusters?.hourly_distribution || []}
                  title="Daily Outage / Incident Frequency Curve (by Hour)"
                />
              </div>
              <div>
                <AvgMttrChart
                  data={clusters?.avg_mttr_by_severity || {}}
                  title="Average Mean Time to Resolution (MTTR)"
                />
              </div>
            </div>

            {/* Outage Vectors / Tags Cloud */}
            <div className="fade-in" style={{ animationDelay: '0.3s' }}>
              <TopTagsCloud tags={clusters?.top_tags || []} />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
