'use client';
/**
 * IncidentCard — card component displaying incident summary.
 */
import Link from 'next/link';
import { Incident } from '@/lib/types';
import StatusBadge, { SeverityBadge } from './StatusBadge';

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export default function IncidentCard({ incident }: { incident: Incident }) {
  const isActive = incident.status === 'open' || incident.status === 'acknowledged' || incident.status === 'investigating';

  return (
    <Link href={`/incidents/${incident.id}`}>
      <div className={`glass-card p-5 hover:border-blue-500/30 transition-all duration-300 cursor-pointer group
        ${isActive ? 'border-l-4 border-l-red-500' : ''}
        ${incident.severity === 'P1' && incident.status === 'open' ? 'pulse-alert' : ''}
      `}>
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <SeverityBadge severity={incident.severity} />
              <StatusBadge status={incident.status} />
              {incident.escalation_count > 0 && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-400">
                  ⬆ Escalated ×{incident.escalation_count}
                </span>
              )}
            </div>
            <h3 className="text-sm font-semibold text-[var(--text-primary)] group-hover:text-blue-400 transition-colors truncate">
              #{incident.id} — {incident.title}
            </h3>
            <p className="text-xs text-[var(--text-muted)] mt-1 line-clamp-2">
              {incident.description}
            </p>
          </div>
          <div className="text-right flex-shrink-0">
            <p className="text-xs text-[var(--text-muted)]">{timeAgo(incident.created_at)}</p>
            <p className="text-xs text-[var(--text-muted)] mt-1">Tier {incident.escalation_tier}</p>
          </div>
        </div>
        <div className="flex items-center gap-4 mt-3 pt-3 border-t border-[var(--border-color)]">
          {incident.tags && (
            <div className="flex gap-1 flex-wrap">
              {incident.tags.split(',').slice(0, 3).map(tag => (
                <span key={tag} className="text-[10px] px-2 py-0.5 rounded bg-[var(--bg-tertiary)] text-[var(--text-muted)]">
                  {tag.trim()}
                </span>
              ))}
            </div>
          )}
          <div className="ml-auto flex items-center gap-2 text-xs text-[var(--text-muted)]">
            {incident.acknowledger_name && <span>👤 {incident.acknowledger_name}</span>}
            <span className="text-[var(--text-muted)]">via {incident.source}</span>
          </div>
        </div>
      </div>
    </Link>
  );
}
