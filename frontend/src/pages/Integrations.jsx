import { useEffect, useState, useMemo } from 'react';
import {
  Plug, Search, ExternalLink, Check, X, RefreshCw, Trash2,
  AlertTriangle, Clock, CheckCircle2, Loader2, ChevronDown, ChevronUp,
} from 'lucide-react';
import { api } from '../api/client';
import { Card } from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';

const CATEGORY_ICONS = {
  cloud: '☁️',
  kubernetes: '⎈',
  observability: '📊',
  database: '🗄️',
  ai_ml: '🤖',
  devtools: '🛠️',
  cdn_streaming: '🌐',
  custom: '⚙️',
};

const STATUS_CONFIG = {
  active: { label: 'Connected', variant: 'success', icon: CheckCircle2 },
  syncing: { label: 'Syncing', variant: 'info', icon: RefreshCw },
  error: { label: 'Error', variant: 'error', icon: AlertTriangle },
  pending: { label: 'Pending', variant: 'warning', icon: Clock },
};

export default function Integrations() {
  const [catalog, setCatalog] = useState([]);
  const [integrations, setIntegrations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [activeCategory, setActiveCategory] = useState('all');
  const [connectModal, setConnectModal] = useState(null); // provider object or null
  const [formData, setFormData] = useState({});
  const [displayName, setDisplayName] = useState('');
  const [connecting, setConnecting] = useState(false);
  const [connectError, setConnectError] = useState('');
  const [syncing, setSyncing] = useState({});
  const [expandedSection, setExpandedSection] = useState('catalog');

  // Load catalog + integrations
  useEffect(() => {
    async function load() {
      try {
        const [catalogRes, integrationsRes] = await Promise.all([
          api.getIntegrationsCatalog(),
          api.listIntegrations(),
        ]);
        setCatalog(catalogRes.categories || []);
        setIntegrations(integrationsRes || []);
      } catch (e) {
        console.error('Failed to load integrations:', e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  // Connected provider keys for status badges on catalog cards
  const connectedProviders = useMemo(() => {
    const map = {};
    integrations.forEach((i) => {
      if (!map[i.provider]) map[i.provider] = [];
      map[i.provider].push(i);
    });
    return map;
  }, [integrations]);

  // Filter catalog
  const filteredCatalog = useMemo(() => {
    return catalog
      .map((cat) => ({
        ...cat,
        providers: cat.providers.filter((p) => {
          const matchesSearch =
            !search ||
            p.display_name.toLowerCase().includes(search.toLowerCase()) ||
            p.key.toLowerCase().includes(search.toLowerCase());
          const matchesCategory =
            activeCategory === 'all' || cat.category === activeCategory;
          return matchesSearch && matchesCategory;
        }),
      }))
      .filter((cat) => cat.providers.length > 0);
  }, [catalog, search, activeCategory]);

  const totalProviders = catalog.reduce((sum, c) => sum + c.providers.length, 0);

  // Open connect modal
  function openConnect(provider) {
    if (provider.status === 'coming_soon') return;
    setConnectModal(provider);
    setFormData({});
    setDisplayName('');
    setConnectError('');
  }

  // Submit connection
  async function handleConnect(e) {
    e.preventDefault();
    if (!connectModal) return;
    setConnecting(true);
    setConnectError('');
    try {
      const res = await api.connectIntegration({
        provider: connectModal.key,
        display_name: displayName || undefined,
        credentials: formData,
      });
      setIntegrations((prev) => [res, ...prev]);
      setConnectModal(null);
    } catch (err) {
      setConnectError(err.message || 'Connection failed');
    } finally {
      setConnecting(false);
    }
  }

  // Sync
  async function handleSync(id) {
    setSyncing((prev) => ({ ...prev, [id]: true }));
    try {
      await api.syncIntegration(id);
      const updated = await api.listIntegrations();
      setIntegrations(updated);
    } catch (e) {
      console.error('Sync failed:', e);
    } finally {
      setSyncing((prev) => ({ ...prev, [id]: false }));
    }
  }

  // Disconnect
  async function handleDisconnect(id) {
    if (!confirm('Disconnect this integration? Cost data will be preserved.')) return;
    try {
      await api.disconnectIntegration(id);
      setIntegrations((prev) => prev.filter((i) => i.id !== id));
    } catch (e) {
      console.error('Disconnect failed:', e);
    }
  }

  if (loading) {
    return (
      <div className="animate-fadeIn">
        <PageHeader title="Integrations" description="Connect your cloud and SaaS providers" icon={Plug} />
        <div className="flex items-center justify-center py-20">
          <Loader2 size={24} className="animate-spin" style={{ color: 'var(--brand-500)' }} />
        </div>
      </div>
    );
  }

  return (
    <div className="animate-fadeIn">
      <PageHeader title="Integrations" description="Connect your cloud and SaaS providers to track costs" icon={Plug}>
        <Badge variant="brand" size="md">{totalProviders} providers</Badge>
        <Badge variant="success" size="md">{integrations.length} connected</Badge>
      </PageHeader>

      {/* Connected Integrations */}
      {integrations.length > 0 && (
        <Card className="mb-6">
          <button
            className="w-full flex items-center justify-between"
            onClick={() => setExpandedSection(expandedSection === 'connected' ? 'catalog' : 'connected')}
          >
            <div className="flex items-center gap-2">
              <h3 className="text-base font-semibold" style={{ color: 'var(--color-text-primary)' }}>
                Active Integrations
              </h3>
              <Badge variant="success">{integrations.length}</Badge>
            </div>
            {expandedSection === 'connected' ? <ChevronUp size={18} style={{ color: 'var(--color-text-tertiary)' }} /> : <ChevronDown size={18} style={{ color: 'var(--color-text-tertiary)' }} />}
          </button>
          {expandedSection === 'connected' && (
            <div className="mt-4 space-y-3">
              {integrations.map((intg) => {
                const st = STATUS_CONFIG[intg.status] || STATUS_CONFIG.pending;
                return (
                  <div
                    key={intg.id}
                    className="flex items-center justify-between p-4 rounded-[var(--radius-md)]"
                    style={{ backgroundColor: 'var(--color-surface-secondary)', border: '1px solid var(--color-border)' }}
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <div
                        className="w-8 h-8 rounded-lg flex items-center justify-center text-white text-xs font-bold flex-shrink-0"
                        style={{ backgroundColor: catalog.flatMap(c => c.providers).find(p => p.key === intg.provider)?.color || '#6B7280' }}
                      >
                        {intg.provider_display_name?.slice(0, 2).toUpperCase()}
                      </div>
                      <div className="min-w-0">
                        <p className="text-sm font-medium truncate" style={{ color: 'var(--color-text-primary)' }}>
                          {intg.display_name || intg.provider_display_name}
                        </p>
                        <div className="flex items-center gap-2 mt-0.5">
                          <span className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>
                            {intg.provider_display_name}
                          </span>
                          {intg.last_sync_at && (
                            <span className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>
                              Synced {new Date(intg.last_sync_at).toLocaleDateString()}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <Badge variant={st.variant} icon={st.icon}>{st.label}</Badge>
                      {intg.sync_error && (
                        <span className="text-xs max-w-[200px] truncate" style={{ color: 'var(--danger-600)' }} title={intg.sync_error}>
                          {intg.sync_error}
                        </span>
                      )}
                      <Button
                        size="sm"
                        variant="secondary"
                        icon={RefreshCw}
                        loading={syncing[intg.id]}
                        onClick={() => handleSync(intg.id)}
                        title="Sync now"
                      >
                        Sync
                      </Button>
                      <button
                        onClick={() => handleDisconnect(intg.id)}
                        className="p-2 rounded-[var(--radius-sm)] transition-colors hover:bg-[var(--color-surface)]"
                        style={{ color: 'var(--color-text-tertiary)' }}
                        title="Disconnect"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </Card>
      )}

      {/* Search & Category Filter */}
      <div className="flex flex-col sm:flex-row gap-3 mb-6">
        <div className="relative flex-1">
          <Search
            size={16}
            className="absolute left-3 top-1/2 -translate-y-1/2"
            style={{ color: 'var(--color-text-tertiary)' }}
          />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search providers..."
            className="w-full pl-9 pr-4 py-2.5 rounded-[var(--radius-md)] text-sm"
            style={{
              backgroundColor: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
              color: 'var(--color-text-primary)',
            }}
          />
        </div>
        <div className="flex gap-1.5 flex-wrap">
          <button
            onClick={() => setActiveCategory('all')}
            className="px-3 py-1.5 rounded-full text-xs font-medium transition-all"
            style={{
              backgroundColor: activeCategory === 'all' ? 'var(--brand-600)' : 'var(--color-surface-secondary)',
              color: activeCategory === 'all' ? '#fff' : 'var(--color-text-secondary)',
              border: `1px solid ${activeCategory === 'all' ? 'var(--brand-600)' : 'var(--color-border)'}`,
            }}
          >
            All
          </button>
          {catalog.map((cat) => (
            <button
              key={cat.category}
              onClick={() => setActiveCategory(cat.category)}
              className="px-3 py-1.5 rounded-full text-xs font-medium transition-all"
              style={{
                backgroundColor: activeCategory === cat.category ? 'var(--brand-600)' : 'var(--color-surface-secondary)',
                color: activeCategory === cat.category ? '#fff' : 'var(--color-text-secondary)',
                border: `1px solid ${activeCategory === cat.category ? 'var(--brand-600)' : 'var(--color-border)'}`,
              }}
            >
              {CATEGORY_ICONS[cat.category] || '📦'} {cat.category_label}
            </button>
          ))}
        </div>
      </div>

      {/* Provider Catalog */}
      {filteredCatalog.map((cat) => (
        <div key={cat.category} className="mb-8">
          <h3
            className="text-sm font-semibold uppercase tracking-wider mb-3 flex items-center gap-2"
            style={{ color: 'var(--color-text-secondary)' }}
          >
            <span>{CATEGORY_ICONS[cat.category] || '📦'}</span>
            {cat.category_label}
            <span className="text-xs font-normal" style={{ color: 'var(--color-text-tertiary)' }}>
              ({cat.providers.length})
            </span>
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
            {cat.providers.map((provider) => {
              const isConnected = connectedProviders[provider.key]?.length > 0;
              const isComingSoon = provider.status === 'coming_soon';
              return (
                <div
                  key={provider.key}
                  className={`relative group rounded-[var(--radius-lg)] p-4 transition-all duration-200 ${
                    isComingSoon ? 'opacity-60' : 'hover:shadow-[var(--shadow-md)] hover:translate-y-[-1px] cursor-pointer'
                  }`}
                  style={{
                    backgroundColor: 'var(--color-surface)',
                    border: `1px solid ${isConnected ? 'var(--color-success-text)' : 'var(--color-border)'}`,
                  }}
                  onClick={() => !isComingSoon && openConnect(provider)}
                >
                  {/* Connected indicator */}
                  {isConnected && (
                    <div className="absolute top-3 right-3">
                      <div
                        className="w-5 h-5 rounded-full flex items-center justify-center"
                        style={{ backgroundColor: 'var(--color-success-bg)' }}
                      >
                        <Check size={12} style={{ color: 'var(--color-success-text)' }} />
                      </div>
                    </div>
                  )}

                  {/* Provider icon + name */}
                  <div className="flex items-center gap-3 mb-3">
                    <div
                      className="w-10 h-10 rounded-lg flex items-center justify-center text-white text-sm font-bold flex-shrink-0"
                      style={{ backgroundColor: provider.color || '#6B7280' }}
                    >
                      {provider.display_name.slice(0, 2).toUpperCase()}
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-semibold truncate" style={{ color: 'var(--color-text-primary)' }}>
                        {provider.display_name}
                      </p>
                      <p className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>
                        {provider.auth_type_label}
                      </p>
                    </div>
                  </div>

                  {/* Action area */}
                  <div className="flex items-center justify-between">
                    {isComingSoon ? (
                      <Badge variant="neutral">Coming Soon</Badge>
                    ) : isConnected ? (
                      <Badge variant="success" icon={CheckCircle2}>
                        {connectedProviders[provider.key].length} connected
                      </Badge>
                    ) : (
                      <span className="text-xs font-medium" style={{ color: 'var(--brand-600)' }}>
                        Connect
                      </span>
                    )}
                    {provider.docs_url && (
                      <a
                        href={provider.docs_url}
                        target="_blank"
                        rel="noreferrer"
                        className="p-1 rounded-[var(--radius-sm)] transition-colors hover:bg-[var(--color-surface-secondary)] opacity-0 group-hover:opacity-100"
                        style={{ color: 'var(--color-text-tertiary)' }}
                        onClick={(e) => e.stopPropagation()}
                        title="View docs"
                      >
                        <ExternalLink size={14} />
                      </a>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ))}

      {filteredCatalog.length === 0 && (
        <div className="text-center py-16">
          <Search size={32} className="mx-auto mb-3" style={{ color: 'var(--color-text-tertiary)' }} />
          <p className="text-sm" style={{ color: 'var(--color-text-tertiary)' }}>
            No providers match your search.
          </p>
        </div>
      )}

      {/* Connect Modal */}
      {connectModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ animation: 'overlayIn 0.2s ease-out' }}>
          <div className="absolute inset-0 bg-black/50" onClick={() => setConnectModal(null)} />
          <div
            className="relative w-full max-w-lg rounded-[var(--radius-lg)] p-6 max-h-[90vh] overflow-y-auto"
            style={{
              backgroundColor: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
              boxShadow: 'var(--shadow-xl)',
            }}
          >
            {/* Modal header */}
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div
                  className="w-10 h-10 rounded-lg flex items-center justify-center text-white text-sm font-bold"
                  style={{ backgroundColor: connectModal.color || '#6B7280' }}
                >
                  {connectModal.display_name.slice(0, 2).toUpperCase()}
                </div>
                <div>
                  <h3 className="text-lg font-semibold" style={{ color: 'var(--color-text-primary)' }}>
                    Connect {connectModal.display_name}
                  </h3>
                  <p className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>
                    {connectModal.auth_type_label}
                  </p>
                </div>
              </div>
              <button
                onClick={() => setConnectModal(null)}
                className="p-2 rounded-[var(--radius-sm)] transition-colors hover:bg-[var(--color-surface-secondary)]"
                style={{ color: 'var(--color-text-tertiary)' }}
              >
                <X size={18} />
              </button>
            </div>

            {/* Form */}
            <form onSubmit={handleConnect} className="space-y-4">
              {/* Display name */}
              <div>
                <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--color-text-secondary)' }}>
                  Display Name <span className="text-xs font-normal" style={{ color: 'var(--color-text-tertiary)' }}>(optional)</span>
                </label>
                <input
                  type="text"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  placeholder={`My ${connectModal.display_name}`}
                  className="w-full px-3 py-2.5 rounded-[var(--radius-md)] text-sm"
                  style={{
                    backgroundColor: 'var(--color-surface-secondary)',
                    border: '1px solid var(--color-border)',
                    color: 'var(--color-text-primary)',
                  }}
                />
              </div>

              {/* Dynamic credential fields */}
              {connectModal.required_fields?.map((field) => (
                <div key={field.name}>
                  <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--color-text-secondary)' }}>
                    {field.label}
                  </label>
                  {field.input_type === 'textarea' ? (
                    <textarea
                      value={formData[field.name] || ''}
                      onChange={(e) => setFormData({ ...formData, [field.name]: e.target.value })}
                      placeholder={field.placeholder}
                      rows={4}
                      className="w-full px-3 py-2.5 rounded-[var(--radius-md)] text-sm font-mono resize-y"
                      style={{
                        backgroundColor: 'var(--color-surface-secondary)',
                        border: '1px solid var(--color-border)',
                        color: 'var(--color-text-primary)',
                      }}
                    />
                  ) : (
                    <input
                      type={field.input_type === 'password' ? 'password' : 'text'}
                      value={formData[field.name] || ''}
                      onChange={(e) => setFormData({ ...formData, [field.name]: e.target.value })}
                      placeholder={field.placeholder}
                      className="w-full px-3 py-2.5 rounded-[var(--radius-md)] text-sm"
                      style={{
                        backgroundColor: 'var(--color-surface-secondary)',
                        border: '1px solid var(--color-border)',
                        color: 'var(--color-text-primary)',
                      }}
                    />
                  )}
                  {field.help_text && (
                    <p className="mt-1 text-xs" style={{ color: 'var(--color-text-tertiary)' }}>
                      {field.help_text}
                    </p>
                  )}
                </div>
              ))}

              {/* Error */}
              {connectError && (
                <div
                  className="p-3 rounded-[var(--radius-md)] flex items-center gap-2 text-sm"
                  style={{ backgroundColor: 'var(--color-error-bg)', color: 'var(--color-error-text)' }}
                >
                  <AlertTriangle size={16} />
                  {connectError}
                </div>
              )}

              {/* Docs link */}
              {connectModal.docs_url && (
                <a
                  href={connectModal.docs_url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1.5 text-xs font-medium"
                  style={{ color: 'var(--brand-600)' }}
                >
                  <ExternalLink size={12} />
                  View setup documentation
                </a>
              )}

              {/* Actions */}
              <div className="flex gap-2 pt-2">
                <Button type="submit" loading={connecting} disabled={connecting}>
                  Connect {connectModal.display_name}
                </Button>
                <Button variant="secondary" onClick={() => setConnectModal(null)} type="button">
                  Cancel
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
