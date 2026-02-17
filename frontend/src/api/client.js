const BASE_URL = '/api/v1';
const V2_BASE_URL = '/api/v2';

async function request(endpoint, options = {}, baseUrl = BASE_URL) {
  const token = localStorage.getItem('cloudpulse_token');
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };
  const res = await fetch(`${baseUrl}${endpoint}`, {
    headers,
    ...options,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || 'API request failed');
  }
  return res.json();
}

export const api = {
  // Dashboard
  getDashboardSummary: () => request('/dashboard/summary'),

  // Accounts
  getAccounts: () => request('/accounts'),

  // Costs
  getCosts: (accountId, startDate, endDate) => {
    const params = new URLSearchParams();
    if (startDate) params.set('start_date', startDate);
    if (endDate) params.set('end_date', endDate);
    return request(`/accounts/${accountId}/costs?${params}`);
  },

  getForecast: (accountId) => request(`/accounts/${accountId}/forecast`),

  // Drill-Down ("Why?")
  getDrillDown: (accountId, mode = 'week') => {
    const params = new URLSearchParams({ mode });
    return request(`/accounts/${accountId}/drill-down?${params}`);
  },

  // Anomalies
  getAnomalies: (accountId, opts = {}) => {
    const params = new URLSearchParams();
    if (opts.startDate) params.set('start_date', opts.startDate);
    if (opts.endDate) params.set('end_date', opts.endDate);
    if (opts.severity) params.set('severity', opts.severity);
    return request(`/accounts/${accountId}/anomalies?${params}`);
  },

  acknowledgeAnomaly: (anomalyId) =>
    request(`/anomalies/${anomalyId}/acknowledge`, { method: 'POST' }),

  // Recommendations
  getRecommendations: (accountId, includeResolved = false) =>
    request(`/accounts/${accountId}/recommendations?include_resolved=${includeResolved}`),

  resolveRecommendation: (recId) =>
    request(`/recommendations/${recId}/resolve`, { method: 'POST' }),

  // AI Insights
  getInsights: (accountId) => request(`/accounts/${accountId}/insights`),

  // Budgets
  getBudgets: (accountId) => request(`/accounts/${accountId}/budgets`),
  createBudget: (accountId, data) =>
    request(`/accounts/${accountId}/budgets`, { method: 'POST', body: JSON.stringify(data) }),
  updateBudget: (budgetId, data) =>
    request(`/budgets/${budgetId}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteBudget: (budgetId) =>
    request(`/budgets/${budgetId}`, { method: 'DELETE' }),
  checkBudgets: (accountId) =>
    request(`/accounts/${accountId}/budgets/check`, { method: 'POST' }),

  // Tags
  getAvailableTags: (accountId) => request(`/accounts/${accountId}/tags`),
  getCostsByTag: (accountId, tagKey) => {
    const params = new URLSearchParams({ tag_key: tagKey });
    return request(`/accounts/${accountId}/tags/costs?${params}`);
  },

  // Shared Reports
  getSharedReports: (accountId) => request(`/accounts/${accountId}/reports`),
  createSharedReport: (accountId) =>
    request(`/accounts/${accountId}/reports`, { method: 'POST' }),

  // AWS CloudFormation setup
  getCloudFormationUrl: () => request('/setup/cloudformation'),
  connectAwsAccount: (roleArn, externalId, accountName) => {
    const params = new URLSearchParams({ role_arn: roleArn, external_id: externalId });
    if (accountName) params.set('account_name', accountName);
    return request(`/setup/connect?${params}`, { method: 'POST' });
  },

  // Alerts
  getAlertConfigs: () => request('/alerts/config'),

  // --- v2 API Tokens ---
  getAPITokens: (page = 1, limit = 25) =>
    request(`/api_tokens?page=${page}&limit=${limit}`, {}, V2_BASE_URL),
  createAPIToken: (data) =>
    request('/api_tokens', { method: 'POST', body: JSON.stringify(data) }, V2_BASE_URL),
  revokeAPIToken: (tokenPrefix) =>
    request(`/api_tokens/${tokenPrefix}`, { method: 'DELETE' }, V2_BASE_URL),

  // --- v2 Cloud Accounts (Multi-Cloud) ---
  getCloudAccounts: (provider) => {
    const params = provider ? `?provider=${provider}` : '';
    return request(`/cloud_accounts${params}`, {}, V2_BASE_URL);
  },
  createCloudAccount: (data) =>
    request('/cloud_accounts', { method: 'POST', body: JSON.stringify(data) }, V2_BASE_URL),
  updateCloudAccount: (id, data) =>
    request(`/cloud_accounts/${id}`, { method: 'PUT', body: JSON.stringify(data) }, V2_BASE_URL),
  deleteCloudAccount: (id) =>
    request(`/cloud_accounts/${id}`, { method: 'DELETE' }, V2_BASE_URL),
  syncCloudAccount: (id, startDate, endDate) => {
    const params = new URLSearchParams();
    if (startDate) params.set('start_date', startDate);
    if (endDate) params.set('end_date', endDate);
    return request(`/cloud_accounts/${id}/sync?${params}`, { method: 'POST' }, V2_BASE_URL);
  },

  // --- v2 Query (DuckDB) ---
  runCostQuery: (data) =>
    request('/query', { method: 'POST', body: JSON.stringify(data) }, V2_BASE_URL),
  getBillingStats: () =>
    request('/query/stats', {}, V2_BASE_URL),
  validateCQL: (filter) =>
    request('/query/validate', { method: 'POST', body: JSON.stringify({ filter }) }, V2_BASE_URL),

  // --- v2 Dashboard ---
  getDashboardSummaryV2: () =>
    request('/dashboard/summary', {}, V2_BASE_URL),

  // --- v2 Cost Query ---
  queryCosts: (data) =>
    request('/query', { method: 'POST', body: JSON.stringify(data) }, V2_BASE_URL),

  // --- v2 Integrations ---
  getIntegrationsCatalog: () =>
    request('/integrations/catalog', {}, V2_BASE_URL),
  listIntegrations: () =>
    request('/integrations', {}, V2_BASE_URL),
  connectIntegration: (data) =>
    request('/integrations/connect', { method: 'POST', body: JSON.stringify(data) }, V2_BASE_URL),
  validateIntegration: (id) =>
    request(`/integrations/${id}/validate`, { method: 'POST' }, V2_BASE_URL),
  syncIntegration: (id) =>
    request(`/integrations/${id}/sync`, { method: 'POST' }, V2_BASE_URL),
  disconnectIntegration: (id) =>
    request(`/integrations/${id}`, { method: 'DELETE' }, V2_BASE_URL),

  // --- v2 Kubernetes ---
  getKubernetesClusters: () =>
    request('/kubernetes/clusters', {}, V2_BASE_URL),
  getKubernetesNamespaces: (clusterId) =>
    request(`/kubernetes/clusters/${clusterId}/namespaces`, {}, V2_BASE_URL),
  getKubernetesRightsizing: (clusterId) =>
    request(`/kubernetes/clusters/${clusterId}/rightsizing`, {}, V2_BASE_URL),
};
