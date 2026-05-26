'use client';
/**
 * Navbar — top navigation bar with real-time notifications.
 */
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useState } from 'react';

export default function Navbar() {
  const { user, logout, token } = useAuth();
  const { isConnected, notifications, clearNotifications } = useWebSocket(token);
  const [showNotifs, setShowNotifs] = useState(false);

  const unreadCount = notifications.length;

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 glass-card border-b border-[var(--border-color)] px-6 py-3">
      <div className="flex items-center justify-between max-w-[1600px] mx-auto">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-3 group">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold text-sm group-hover:shadow-lg group-hover:shadow-blue-500/30 transition-all duration-300">
            IM
          </div>
          <span className="text-lg font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            Incident Manager
          </span>
        </Link>

        {/* Right side */}
        <div className="flex items-center gap-4">
          {/* Connection status */}
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-emerald-400 shadow-lg shadow-emerald-400/50' : 'bg-red-400 shadow-lg shadow-red-400/50'}`} />
            <span className="text-xs text-[var(--text-muted)]">
              {isConnected ? 'Live' : 'Offline'}
            </span>
          </div>

          {/* Notifications */}
          <div className="relative">
            <button
              onClick={() => setShowNotifs(!showNotifs)}
              className="relative p-2 rounded-lg hover:bg-[var(--bg-tertiary)] transition-colors"
            >
              <svg className="w-5 h-5 text-[var(--text-secondary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-red-500 text-white text-xs flex items-center justify-center font-bold pulse-alert">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </button>

            {showNotifs && (
              <div className="absolute right-0 top-12 w-96 glass-card p-4 slide-in max-h-96 overflow-y-auto">
                <div className="flex justify-between items-center mb-3">
                  <h3 className="text-sm font-semibold">Notifications</h3>
                  <button onClick={clearNotifications} className="text-xs text-blue-400 hover:text-blue-300">
                    Clear all
                  </button>
                </div>
                {notifications.length === 0 ? (
                  <p className="text-sm text-[var(--text-muted)] py-4 text-center">No notifications</p>
                ) : (
                  <div className="space-y-2">
                    {notifications.slice(0, 10).map((notif, i) => (
                      <div key={i} className="p-3 rounded-lg bg-[var(--bg-secondary)] text-sm fade-in">
                        <p>{notif.data.message}</p>
                        <p className="text-xs text-[var(--text-muted)] mt-1">
                          {notif.data.timestamp ? new Date(notif.data.timestamp).toLocaleTimeString() : ''}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* User */}
          {user && (
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-white text-xs font-bold">
                {user.name.charAt(0).toUpperCase()}
              </div>
              <div className="hidden md:block">
                <p className="text-sm font-medium">{user.name}</p>
                <p className="text-xs text-[var(--text-muted)] capitalize">{user.role} · T{user.tier}</p>
              </div>
              <button
                onClick={logout}
                className="text-xs text-[var(--text-muted)] hover:text-red-400 transition-colors ml-2"
              >
                Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}
