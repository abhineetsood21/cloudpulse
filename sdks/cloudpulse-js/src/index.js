/**
 * CloudPulse JavaScript SDK
 *
 * Lightweight client for the CloudPulse v2 API.
 * Works in Node.js 18+ and modern browsers (uses native fetch).
 *
 * @example
 * const { CloudPulseClient } = require('@cloudpulse/js');
 * const client = new CloudPulseClient({ apiToken: 'cpls_...' });
 * const workspaces = await client.workspaces.list();
 */

class CloudPulseClient {
  constructor({ apiToken, baseUrl = 'https://api.cloudpulse.dev' }) {
    this._baseUrl = `${baseUrl.replace(/\/$/, '')}/api/v2`;
    this._headers = {
      Authorization: `Bearer ${apiToken}`,
      'Content-Type': 'application/json',
      'User-Agent': 'cloudpulse-js/0.1.0',
    };

    this.workspaces = new Resource(this, '/workspaces', 'workspaces');
    this.costReports = new Resource(this, '/cost_reports', 'cost_reports');
    this.folders = new Resource(this, '/folders', 'folders');
    this.savedFilters = new Resource(this, '/saved_filters', 'saved_filters');
    this.dashboards = new Resource(this, '/dashboards', 'dashboards');
    this.segments = new Resource(this, '/segments', 'segments');
    this.teams = new Resource(this, '/teams', 'teams');
    this.accessGrants = new Resource(this, '/access_grants', 'access_grants');
    this.virtualTags = new Resource(this, '/virtual_tags', 'virtual_tags');
    this.apiTokens = new TokensResource(this);
    this.resourceReports = new Resource(this, '/resource_reports', 'resource_reports');
  }

  async request(method, path, body, params) {
    let url = `${this._baseUrl}${path}`;
    if (params) {
      const qs = new URLSearchParams();
      for (const [k, v] of Object.entries(params)) {
        if (v !== undefined && v !== null) qs.set(k, String(v));
      }
      const qsStr = qs.toString();
      if (qsStr) url += `?${qsStr}`;
    }

    const res = await fetch(url, {
      method,
      headers: this._headers,
      body: body ? JSON.stringify(body) : undefined,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(`CloudPulse API error ${res.status}: ${err.detail || 'Unknown error'}`);
    }

    return res.json();
  }
}

class Resource {
  constructor(client, basePath, listKey) {
    this._client = client;
    this._basePath = basePath;
    this._listKey = listKey;
  }

  list(params) {
    return this._client.request('GET', this._basePath, null, params);
  }

  get(token) {
    return this._client.request('GET', `${this._basePath}/${token}`);
  }

  create(data) {
    return this._client.request('POST', this._basePath, data);
  }

  update(token, data) {
    return this._client.request('PUT', `${this._basePath}/${token}`, data);
  }

  delete(token) {
    return this._client.request('DELETE', `${this._basePath}/${token}`);
  }
}

class TokensResource {
  constructor(client) {
    this._client = client;
  }

  list(params) {
    return this._client.request('GET', '/api_tokens', null, params);
  }

  create(data) {
    return this._client.request('POST', '/api_tokens', data);
  }

  revoke(tokenPrefix) {
    return this._client.request('DELETE', `/api_tokens/${tokenPrefix}`);
  }
}

module.exports = { CloudPulseClient };
