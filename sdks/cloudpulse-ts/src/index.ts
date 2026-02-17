/**
 * CloudPulse TypeScript SDK
 *
 * @example
 * ```ts
 * import { CloudPulseClient } from '@cloudpulse/sdk';
 * const client = new CloudPulseClient({ apiToken: 'cpls_...' });
 * const workspaces = await client.workspaces.list();
 * ```
 */

// --- Types ---

export interface Workspace {
  token: string;
  name: string;
  is_default: boolean;
  created_at: string;
}

export interface CostReport {
  token: string;
  title: string;
  workspace_token?: string;
  folder_token?: string;
  filter?: string;
  groupings: string;
  date_interval: string;
  date_bucket: string;
  start_date?: string;
  end_date?: string;
  settings: Record<string, unknown>;
  created_at: string;
}

export interface Folder {
  token: string;
  title: string;
  workspace_token?: string;
  parent_folder_token?: string;
  created_at: string;
}

export interface SavedFilter {
  token: string;
  title: string;
  filter: string;
  created_at: string;
}

export interface Dashboard {
  token: string;
  title: string;
  widgets: Record<string, unknown>[];
  date_interval: string;
  start_date?: string;
  end_date?: string;
  created_at: string;
}

export interface Segment {
  token: string;
  title: string;
  description?: string;
  filter?: string;
  priority: number;
  track_unallocated: boolean;
  created_at: string;
}

export interface Team {
  token: string;
  name: string;
  description?: string;
  created_at: string;
}

export interface AccessGrant {
  token: string;
  team_token?: string;
  resource_type: string;
  resource_token: string;
  access_level: string;
  created_at: string;
}

export interface VirtualTag {
  token: string;
  key: string;
  description?: string;
  overridable: boolean;
  backfill_until?: string;
  values: Record<string, unknown>[];
  created_at: string;
}

export interface APIToken {
  token_prefix: string;
  name: string;
  scopes: string;
  is_active: boolean;
  last_used_at?: string;
  created_at: string;
}

export interface APITokenCreated extends APIToken {
  token: string;
}

export interface ResourceReport {
  token: string;
  title: string;
  filter?: string;
  groupings: string;
  columns: string[];
  created_at: string;
}

export interface PaginatedList<T> {
  links: Record<string, string>;
  [key: string]: T[] | Record<string, string>;
}

export interface Message {
  message: string;
}

// --- Client ---

export interface CloudPulseClientOptions {
  apiToken: string;
  baseUrl?: string;
}

class Resource {
  constructor(private client: CloudPulseClient) {}

  protected async get<T>(path: string, params?: Record<string, string | number>): Promise<T> {
    return this.client.request('GET', path, undefined, params);
  }

  protected async post<T>(path: string, data: Record<string, unknown>): Promise<T> {
    return this.client.request('POST', path, data);
  }

  protected async put<T>(path: string, data: Record<string, unknown>): Promise<T> {
    return this.client.request('PUT', path, data);
  }

  protected async del<T>(path: string): Promise<T> {
    return this.client.request('DELETE', path);
  }
}

class WorkspacesResource extends Resource {
  list(params?: { page?: number; limit?: number }) {
    return this.get<{ workspaces: Workspace[]; links: Record<string, string> }>('/workspaces', params as any);
  }
  get(token: string) { return this.get<Workspace>(`/workspaces/${token}`); }
  create(data: { name: string }) { return this.post<Workspace>('/workspaces', data); }
  update(token: string, data: { name: string }) { return this.put<Workspace>(`/workspaces/${token}`, data); }
  delete(token: string) { return this.del<Message>(`/workspaces/${token}`); }
}

class CostReportsResource extends Resource {
  list(params?: { workspace_token?: string; page?: number; limit?: number }) {
    return this.get<{ cost_reports: CostReport[]; links: Record<string, string> }>('/cost_reports', params as any);
  }
  get(token: string) { return this.get<CostReport>(`/cost_reports/${token}`); }
  create(data: Record<string, unknown>) { return this.post<CostReport>('/cost_reports', data); }
  update(token: string, data: Record<string, unknown>) { return this.put<CostReport>(`/cost_reports/${token}`, data); }
  delete(token: string) { return this.del<Message>(`/cost_reports/${token}`); }
}

class FoldersResource extends Resource {
  list(params?: { workspace_token?: string; page?: number; limit?: number }) {
    return this.get<{ folders: Folder[]; links: Record<string, string> }>('/folders', params as any);
  }
  get(token: string) { return this.get<Folder>(`/folders/${token}`); }
  create(data: Record<string, unknown>) { return this.post<Folder>('/folders', data); }
  update(token: string, data: Record<string, unknown>) { return this.put<Folder>(`/folders/${token}`, data); }
  delete(token: string) { return this.del<Message>(`/folders/${token}`); }
}

class SegmentsResource extends Resource {
  list(params?: { workspace_token?: string; page?: number; limit?: number }) {
    return this.get<{ segments: Segment[]; links: Record<string, string> }>('/segments', params as any);
  }
  get(token: string) { return this.get<Segment>(`/segments/${token}`); }
  create(data: Record<string, unknown>) { return this.post<Segment>('/segments', data); }
  update(token: string, data: Record<string, unknown>) { return this.put<Segment>(`/segments/${token}`, data); }
  delete(token: string) { return this.del<Message>(`/segments/${token}`); }
}

class TeamsResource extends Resource {
  list(params?: { workspace_token?: string; page?: number; limit?: number }) {
    return this.get<{ teams: Team[]; links: Record<string, string> }>('/teams', params as any);
  }
  get(token: string) { return this.get<Team>(`/teams/${token}`); }
  create(data: Record<string, unknown>) { return this.post<Team>('/teams', data); }
  update(token: string, data: Record<string, unknown>) { return this.put<Team>(`/teams/${token}`, data); }
  delete(token: string) { return this.del<Message>(`/teams/${token}`); }
}

class VirtualTagsResource extends Resource {
  list(params?: { workspace_token?: string; page?: number; limit?: number }) {
    return this.get<{ virtual_tags: VirtualTag[]; links: Record<string, string> }>('/virtual_tags', params as any);
  }
  get(token: string) { return this.get<VirtualTag>(`/virtual_tags/${token}`); }
  create(data: Record<string, unknown>) { return this.post<VirtualTag>('/virtual_tags', data); }
  update(token: string, data: Record<string, unknown>) { return this.put<VirtualTag>(`/virtual_tags/${token}`, data); }
  delete(token: string) { return this.del<Message>(`/virtual_tags/${token}`); }
}

class APITokensResource extends Resource {
  list(params?: { page?: number; limit?: number }) {
    return this.get<{ api_tokens: APIToken[]; links: Record<string, string> }>('/api_tokens', params as any);
  }
  create(data: { name: string; scopes?: string }) { return this.post<APITokenCreated>('/api_tokens', data); }
  revoke(tokenPrefix: string) { return this.del<Message>(`/api_tokens/${tokenPrefix}`); }
}

export class CloudPulseClient {
  private baseUrl: string;
  private headers: Record<string, string>;

  workspaces: WorkspacesResource;
  costReports: CostReportsResource;
  folders: FoldersResource;
  segments: SegmentsResource;
  teams: TeamsResource;
  virtualTags: VirtualTagsResource;
  apiTokens: APITokensResource;

  constructor(options: CloudPulseClientOptions) {
    this.baseUrl = `${(options.baseUrl || 'https://api.cloudpulse.dev').replace(/\/$/, '')}/api/v2`;
    this.headers = {
      'Authorization': `Bearer ${options.apiToken}`,
      'Content-Type': 'application/json',
      'User-Agent': 'cloudpulse-ts/0.1.0',
    };

    this.workspaces = new WorkspacesResource(this);
    this.costReports = new CostReportsResource(this);
    this.folders = new FoldersResource(this);
    this.segments = new SegmentsResource(this);
    this.teams = new TeamsResource(this);
    this.virtualTags = new VirtualTagsResource(this);
    this.apiTokens = new APITokensResource(this);
  }

  async request<T>(method: string, path: string, body?: unknown, params?: Record<string, string | number>): Promise<T> {
    let url = `${this.baseUrl}${path}`;
    if (params) {
      const qs = new URLSearchParams();
      for (const [k, v] of Object.entries(params)) {
        if (v !== undefined) qs.set(k, String(v));
      }
      const qsStr = qs.toString();
      if (qsStr) url += `?${qsStr}`;
    }

    const res = await fetch(url, {
      method,
      headers: this.headers,
      body: body ? JSON.stringify(body) : undefined,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(`CloudPulse API error ${res.status}: ${err.detail || 'Unknown error'}`);
    }

    return res.json() as Promise<T>;
  }
}
