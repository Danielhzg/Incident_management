'use client';

import { Incident } from '@/lib/types';

interface TimelineEvent {
  title: string;
  time: string | null;
  description: string;
  icon: string;
  color: string;
}

export default function Timeline({ incident }: { incident: Incident }) {
  const events: TimelineEvent[] = [
    {
      title: 'Incident Detected',
      time: incident.created_at,
      description: `Triggered automatically via ${incident.source}.`,
      icon: '🚨',
      color: 'border-red-500 bg-red-500/10 text-red-400',
    },
  ];

  if (incident.acknowledged_at) {
    events.push({
      title: 'Acknowledged',
      time: incident.acknowledged_at,
      description: `Acknowledged by ${incident.acknowledger_name || 'Engineer'}. Response time: ${calculateDuration(incident.created_at, incident.acknowledged_at)}.`,
      icon: '👤',
      color: 'border-blue-500 bg-blue-500/10 text-blue-400',
    });
  } else if (incident.status === 'open') {
    events.push({
      title: 'Awaiting Acknowledgment',
      time: null,
      description: 'SLA is ticking. On-call engineer notified.',
      icon: '⏳',
      color: 'border-amber-500 bg-amber-500/10 text-amber-400 animate-pulse',
    });
  }

  if (incident.escalation_count > 0) {
    events.push({
      title: `Escalated to Tier ${incident.escalation_tier}`,
      time: incident.updated_at, // Use update time as approximation of escalation time
      description: `Auto-escalated ${incident.escalation_count} time(s) due to lack of acknowledgment within SLA.`,
      icon: '⬆️',
      color: 'border-purple-500 bg-purple-500/10 text-purple-400',
    });
  }

  if (incident.resolved_at) {
    events.push({
      title: 'Incident Resolved',
      time: incident.resolved_at,
      description: `Marked resolved by ${incident.resolver_name || 'Engineer'}. Total time to resolution (TTR): ${calculateDuration(incident.created_at, incident.resolved_at)}.`,
      icon: '✅',
      color: 'border-emerald-500 bg-emerald-500/10 text-emerald-400',
    });
  }

  function calculateDuration(startStr: string, endStr: string): string {
    const diff = new Date(endStr).getTime() - new Date(startStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'less than a minute';
    if (mins < 60) return `${mins} minutes`;
    const hours = Math.floor(mins / 60);
    const remainingMins = mins % 60;
    return `${hours}h ${remainingMins}m`;
  }

  return (
    <div className="relative border-l-2 border-slate-800 ml-3 pl-6 space-y-6">
      {events.map((event, index) => (
        <div key={index} className="relative fade-in" style={{ animationDelay: `${index * 0.1}s` }}>
          {/* Node Icon */}
          <span className={`absolute -left-10 top-0.5 w-8 h-8 rounded-full border-2 flex items-center justify-center text-sm shadow-md ${event.color}`}>
            {event.icon}
          </span>

          {/* Event Content */}
          <div className="glass-card p-4 hover:border-slate-700/50 transition-colors">
            <div className="flex justify-between items-start gap-4 flex-wrap">
              <h4 className="font-semibold text-sm text-slate-200">{event.title}</h4>
              {event.time && (
                <span className="text-[11px] text-[var(--text-muted)]">
                  {new Date(event.time).toLocaleString()}
                </span>
              )}
            </div>
            <p className="text-xs text-[var(--text-secondary)] mt-1">{event.description}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
