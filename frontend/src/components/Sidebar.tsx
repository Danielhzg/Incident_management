'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';

export default function Sidebar() {
  const pathname = usePathname();
  const { user } = useAuth();

  const links = [
    { href: '/', label: 'Dashboard' },
    { href: '/incidents', label: 'Incidents' },
    { href: '/analytics', label: 'AI Analytics' },
  ];

  return (
    <aside className="fixed top-0 left-0 bottom-0 w-64 bg-[var(--bg-secondary)] border-r border-[var(--border-color)] p-4 hidden md:flex flex-col justify-between z-40 pt-20">
      <div className="space-y-6">
        <div>
          <p className="text-[10px] font-semibold text-[var(--text-muted)] uppercase tracking-wider px-3 mb-3">
            Navigation
          </p>
          <nav className="space-y-1">
            {links.map((link) => {
              const active = pathname === link.href || (link.href !== '/' && pathname.startsWith(link.href));
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`block px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                    active
                      ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                      : 'text-[var(--text-secondary)] hover:text-white hover:bg-[var(--bg-tertiary)]'
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="border-t border-[var(--border-color)] pt-6">
          <p className="text-[10px] font-semibold text-[var(--text-muted)] uppercase tracking-wider px-3 mb-3">
            On-Call Status
          </p>
          <div className="mx-3 p-3.5 rounded-xl bg-[var(--bg-tertiary)] border border-[var(--border-color)] space-y-2.5">
            <div className="flex items-center gap-2">
              <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-xs font-semibold text-emerald-400">Shift Active</span>
            </div>
            <div className="text-[11px] text-[var(--text-muted)]">
              Primary Tier: <span className="font-semibold text-slate-300">Tier 1</span>
            </div>
            <div className="text-[11px] text-[var(--text-muted)]">
              Secondary: <span className="font-semibold text-slate-300">Tier 2</span>
            </div>
          </div>
        </div>
      </div>

      {user && (
        <div className="p-3 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-xl flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-white text-xs font-bold shadow-md shadow-blue-500/10">
            {user.name.charAt(0).toUpperCase()}
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-xs font-bold text-slate-200 truncate">{user.name}</p>
            <p className="text-[10px] text-[var(--text-muted)] capitalize truncate">
              {user.role} · Tier {user.tier}
            </p>
          </div>
        </div>
      )}
    </aside>
  );
}
