/**
 * TypeScript type definitions for the Incident Management System.
 */

// ── Enums ────────────────────────────────────────────────
export type IncidentSeverity = 'P1' | 'P2' | 'P3' | 'P4';
export type IncidentStatus = 'open' | 'acknowledged' | 'investigating' | 'resolved' | 'closed';
export type UserRole = 'engineer' | 'lead' | 'manager';
export type UserTier = 1 | 2 | 3;

// ── Models ───────────────────────────────────────────────
export interface User {
  id: number;
  email: string;
  name: string;
  role: UserRole;
  tier: UserTier;
  is_active: boolean;
  created_at: string;
}

export interface Incident {
  id: number;
  title: string;
  description: string;
  severity: IncidentSeverity;
  status: IncidentStatus;
  source: string;
  tags: string | null;
  assigned_to: number | null;
  acknowledged_by: number | null;
  resolved_by: number | null;
  escalation_tier: number;
  escalation_count: number;
  created_at: string;
  updated_at: string;
  acknowledged_at: string | null;
  resolved_at: string | null;
  assignee_name: string | null;
  acknowledger_name: string | null;
  resolver_name: string | null;
}

export interface PostMortem {
  id: number;
  incident_id: number;
  title: string;
  summary: string;
  root_cause: string;
  impact: string;
  timeline: string;
  action_items: string;
  lessons_learned: string | null;
  generated_by_ai: boolean;
  ai_model: string | null;
  created_at: string;
}

// ── API Responses ────────────────────────────────────────
export interface IncidentListResponse {
  incidents: Incident[];
  total: number;
  page: number;
  per_page: number;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface IncidentStats {
  total_incidents: number;
  by_status: Record<string, number>;
  by_severity: Record<string, number>;
  avg_ttr_seconds: number | null;
}

export interface ClusterData {
  total_analyzed: number;
  severity_distribution: Record<string, number>;
  status_distribution: Record<string, number>;
  source_distribution: Record<string, number>;
  avg_mttr_by_severity: Record<string, number | null>;
  top_tags: { tag: string; count: number }[];
  hourly_distribution: number[];
  peak_hour: number | null;
}

export interface InsightsData {
  insights: { insight: string; severity: string; recommendation: string }[] | string;
  clusters: ClusterData;
}

// ── WebSocket Messages ───────────────────────────────────
export interface WSMessage {
  type: 'connected' | 'incident_created' | 'incident_acknowledged' | 'incident_resolved' | 'incident_escalated' | 'pong';
  data: {
    message?: string;
    incident_id?: number;
    title?: string;
    severity?: string;
    engineer_name?: string;
    resolver_name?: string;
    timestamp?: string;
    [key: string]: unknown;
  };
}

// ── Request DTOs ─────────────────────────────────────────
export interface CreateIncidentDTO {
  title: string;
  description: string;
  severity: IncidentSeverity;
  source?: string;
  tags?: string;
}

export interface LoginDTO {
  email: string;
  password: string;
}
