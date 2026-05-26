/**
 * StatusBadge — colored badge for incident status.
 */
import { IncidentStatus } from '@/lib/types';

const statusConfig: Record<IncidentStatus, { label: string; bg: string; text: string; dot: string }> = {
  open: { label: 'Open', bg: 'bg-red-500/15', text: 'text-red-400', dot: 'bg-red-400' },
  acknowledged: { label: 'Acknowledged', bg: 'bg-blue-500/15', text: 'text-blue-400', dot: 'bg-blue-400' },
  investigating: { label: 'Investigating', bg: 'bg-amber-500/15', text: 'text-amber-400', dot: 'bg-amber-400' },
  resolved: { label: 'Resolved', bg: 'bg-emerald-500/15', text: 'text-emerald-400', dot: 'bg-emerald-400' },
  closed: { label: 'Closed', bg: 'bg-slate-500/15', text: 'text-slate-400', dot: 'bg-slate-400' },
};

export default function StatusBadge({ status }: { status: IncidentStatus }) {
  const config = statusConfig[status];
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${config.bg} ${config.text}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${config.dot} ${status === 'open' ? 'animate-pulse' : ''}`} />
      {config.label}
    </span>
  );
}

/**
 * SeverityBadge — colored badge for incident severity.
 */
import { IncidentSeverity } from '@/lib/types';

const severityConfig: Record<IncidentSeverity, { label: string; bg: string; text: string }> = {
  P1: { label: 'P1 Critical', bg: 'bg-red-500/20', text: 'text-red-400' },
  P2: { label: 'P2 High', bg: 'bg-orange-500/20', text: 'text-orange-400' },
  P3: { label: 'P3 Medium', bg: 'bg-yellow-500/20', text: 'text-yellow-400' },
  P4: { label: 'P4 Low', bg: 'bg-green-500/20', text: 'text-green-400' },
};

export function SeverityBadge({ severity }: { severity: IncidentSeverity }) {
  const config = severityConfig[severity];
  return (
    <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold ${config.bg} ${config.text}`}>
      {config.label}
    </span>
  );
}
