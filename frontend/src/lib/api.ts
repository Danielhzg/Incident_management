/**
 * API client for the Incident Management System backend.
 */
import {
  Incident, IncidentListResponse, TokenResponse, IncidentStats,
  PostMortem, ClusterData, InsightsData, User,
  CreateIncidentDTO, LoginDTO, IncidentSeverity, IncidentStatus,
} from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiClient {
  private token: string | null = null;

  constructor() {
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('token');
    }
  }

  setToken(token: string) {
    this.token = token;
    if (typeof window !== 'undefined') {
      localStorage.setItem('token', token);
    }
  }

  clearToken() {
    this.token = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token');
    }
  }

  private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> || {}),
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    if (response.status === 204) {
      return undefined as T;
    }

    return response.json();
  }

  // ── Auth ──────────────────────────────────────────────
  async login(data: LoginDTO): Promise<TokenResponse> {
    const result = await this.request<TokenResponse>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    this.setToken(result.access_token);
    return result;
  }

  async register(data: { email: string; name: string; password: string; role?: string; tier?: number }): Promise<TokenResponse> {
    const result = await this.request<TokenResponse>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    this.setToken(result.access_token);
    return result;
  }

  async getMe(): Promise<User> {
    return this.request<User>('/api/auth/me');
  }

  async getUsers(): Promise<User[]> {
    return this.request<User[]>('/api/auth/users');
  }

  // ── Incidents ─────────────────────────────────────────
  async listIncidents(params?: {
    page?: number;
    per_page?: number;
    severity?: IncidentSeverity;
    status?: IncidentStatus;
    search?: string;
  }): Promise<IncidentListResponse> {
    const query = new URLSearchParams();
    if (params?.page) query.set('page', String(params.page));
    if (params?.per_page) query.set('per_page', String(params.per_page));
    if (params?.severity) query.set('severity', params.severity);
    if (params?.status) query.set('status', params.status);
    if (params?.search) query.set('search', params.search);
    const qs = query.toString();
    return this.request<IncidentListResponse>(`/api/incidents/${qs ? `?${qs}` : ''}`);
  }

  async getIncident(id: number): Promise<Incident> {
    return this.request<Incident>(`/api/incidents/${id}`);
  }

  async createIncident(data: CreateIncidentDTO): Promise<Incident> {
    return this.request<Incident>('/api/incidents/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async acknowledgeIncident(id: number): Promise<{ status: string; message: string }> {
    return this.request(`/api/incidents/${id}/acknowledge`, {
      method: 'POST',
      body: JSON.stringify({}),
    });
  }

  async resolveIncident(id: number, resolution_notes: string): Promise<{ status: string; message: string }> {
    return this.request(`/api/incidents/${id}/resolve`, {
      method: 'POST',
      body: JSON.stringify({ resolution_notes }),
    });
  }

  async closeIncident(id: number, notes?: string): Promise<{ status: string; message: string }> {
    return this.request(`/api/incidents/${id}/close`, {
      method: 'POST',
      body: JSON.stringify({ notes: notes ?? null }),
    });
  }

  async deleteIncident(id: number): Promise<void> {
    return this.request(`/api/incidents/${id}`, { method: 'DELETE' });
  }

  async getStats(): Promise<IncidentStats> {
    return this.request<IncidentStats>('/api/incidents/stats');
  }

  // ── Analytics ─────────────────────────────────────────
  async generatePostMortem(incidentId: number): Promise<PostMortem> {
    return this.request<PostMortem>(`/api/analytics/postmortem/${incidentId}`, {
      method: 'POST',
    });
  }

  async getPostMortems(incidentId: number): Promise<PostMortem[]> {
    return this.request<PostMortem[]>(`/api/analytics/postmortem/${incidentId}`);
  }

  async getClusters(): Promise<ClusterData> {
    return this.request<ClusterData>('/api/analytics/clusters');
  }

  async getInsights(): Promise<InsightsData> {
    return this.request<InsightsData>('/api/analytics/insights');
  }
}

export const api = new ApiClient();
export default api;
