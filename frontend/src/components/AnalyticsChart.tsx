'use client';

interface BarChartProps {
  data: Record<string, number | null>;
  title: string;
  valueSuffix?: string;
  colorClass?: string;
}

export function AvgMttrChart({ data, title, valueSuffix = 'm', colorClass = 'from-blue-500 to-cyan-500' }: BarChartProps) {
  const keys = ['P1', 'P2', 'P3', 'P4'];
  const values = keys.map(k => {
    const val = data[k];
    if (val === null || val === undefined) return 0;
    // TTR is in seconds in database stats, or in minutes. Let's round to nearest unit.
    return Math.round(val / 60); // Convert seconds to minutes
  });

  const maxVal = Math.max(...values, 10); // Avoid dividing by zero

  return (
    <div className="glass-card p-5 border-slate-800">
      <h3 className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-4">
        {title}
      </h3>
      <div className="space-y-4">
        {keys.map((key, i) => {
          const val = values[i];
          const percentage = (val / maxVal) * 100;
          return (
            <div key={key} className="space-y-1">
              <div className="flex justify-between items-center text-xs">
                <span className="font-semibold text-slate-300">{key}</span>
                <span className="text-[var(--text-muted)] font-medium">
                  {val > 0 ? `${val}${valueSuffix}` : 'N/A'}
                </span>
              </div>
              <div className="w-full bg-[var(--bg-tertiary)] h-3 rounded-full overflow-hidden border border-[var(--border-color)]">
                <div
                  className={`bg-gradient-to-r ${colorClass} h-full rounded-full transition-all duration-1000`}
                  style={{ width: val > 0 ? `${percentage}%` : '0%' }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

interface HourlyChartProps {
  data: number[];
  title: string;
}

export function HourlyDistributionChart({ data, title }: HourlyChartProps) {
  const hours = data || Array(24).fill(0);
  const maxCount = Math.max(...hours, 1);

  return (
    <div className="glass-card p-5 border-slate-800">
      <h3 className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-4">
        {title}
      </h3>
      {/* SVG Column Chart */}
      <div className="h-48 flex items-end gap-1.5 pt-4 pb-2 border-b border-[var(--border-color)]">
        {hours.map((count, hour) => {
          const pct = (count / maxCount) * 85; // Max 85% height to fit numbers
          return (
            <div key={hour} className="flex-1 flex flex-col items-center group h-full justify-end relative">
              {/* Tooltip */}
              <div className="absolute bottom-full mb-2 hidden group-hover:flex flex-col items-center z-10">
                <div className="bg-slate-900 border border-slate-800 text-[10px] text-white px-2 py-1 rounded shadow-xl whitespace-nowrap">
                  {hour}:00 — {count} incidents
                </div>
                <div className="w-1.5 h-1.5 bg-slate-900 border-r border-b border-slate-800 rotate-45 -mt-1" />
              </div>

              {/* Bar */}
              <div
                style={{ height: `${pct}%` }}
                className="w-full bg-gradient-to-t from-purple-600/70 to-blue-500/80 hover:from-purple-500 hover:to-blue-400 rounded-t-sm transition-all duration-500"
              />
            </div>
          );
        })}
      </div>
      {/* X Axis Labels */}
      <div className="flex justify-between items-center text-[9px] text-[var(--text-muted)] mt-2 font-mono px-1">
        <span>00:00</span>
        <span>06:00</span>
        <span>12:00</span>
        <span>18:00</span>
        <span>23:00</span>
      </div>
    </div>
  );
}

interface TagCloudProps {
  tags: { tag: string; count: number }[];
}

export function TopTagsCloud({ tags }: TagCloudProps) {
  const sortedTags = tags || [];
  const maxCount = sortedTags.length > 0 ? sortedTags[0].count : 1;

  return (
    <div className="glass-card p-5 border-slate-800">
      <h3 className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-4">
        Top Incident Vectors (Tags)
      </h3>
      <div className="flex flex-wrap gap-2 pt-2">
        {sortedTags.map(({ tag, count }) => {
          // Dynamic scale based on counts
          const intensity = Math.max(0.3, count / maxCount);
          return (
            <span
              key={tag}
              style={{
                borderColor: `rgba(59, 130, 246, ${intensity * 0.4})`,
                backgroundColor: `rgba(59, 130, 246, ${intensity * 0.1})`,
                color: `rgba(147, 197, 253, ${Math.max(0.7, intensity)})`,
              }}
              className="text-xs px-2.5 py-1 rounded-lg border font-semibold transition-all hover:scale-105"
            >
              #{tag} <span className="text-[10px] text-[var(--text-muted)] font-normal ml-0.5">({count})</span>
            </span>
          );
        })}
        {sortedTags.length === 0 && (
          <p className="text-xs text-[var(--text-muted)]">No tags catalogued yet.</p>
        )}
      </div>
    </div>
  );
}
