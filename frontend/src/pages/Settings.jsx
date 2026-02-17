import { useEffect, useState } from 'react';
import { Settings, User, Cloud, Bell, Palette, Info, ExternalLink, Copy, Check, Key, Plus, Trash2, Eye, EyeOff, Shield, Plug } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { api } from '../api/client';
import { Card, CardTitle } from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';


export default function SettingsPage() {
  const { user } = useAuth();
  const { theme, setTheme, isDark } = useTheme();
  const [accounts, setAccounts] = useState([]);
  const [copied, setCopied] = useState(false);
  const [activeSection, setActiveSection] = useState('profile');

  // API Keys state
  const [apiTokens, setApiTokens] = useState([]);
  const [showCreateToken, setShowCreateToken] = useState(false);
  const [newTokenName, setNewTokenName] = useState('');
  const [newTokenScopes, setNewTokenScopes] = useState('read');
  const [createdToken, setCreatedToken] = useState(null);
  const [tokenVisible, setTokenVisible] = useState(false);
  const [tokenCopied, setTokenCopied] = useState(false);
  const [loadingTokens, setLoadingTokens] = useState(false);
  const [showConnectFlow, setShowConnectFlow] = useState(false);
  const [externalId, setExternalId] = useState('');
  const [roleArn, setRoleArn] = useState('');
  const [connectingAws, setConnectingAws] = useState(false);
  const [connectError, setConnectError] = useState('');

  function handleDownloadTemplate() {
    // Generate a unique external ID for this connection
    const eid = crypto.randomUUID();
    setExternalId(eid);
    window.open('/static/cloudpulse-iam-role.yaml', '_blank');
  }

  async function handleSubmitRoleArn() {
    if (!roleArn.trim() || !externalId) return;
    setConnectingAws(true);
    setConnectError('');
    try {
      const params = new URLSearchParams({ role_arn: roleArn, external_id: externalId });
      const data = await api.connectAwsAccount(roleArn, externalId);
      setShowConnectFlow(false);
      setRoleArn('');
      api.getAccounts().then(setAccounts).catch(console.error);
    } catch (e) {
      setConnectError(e.message || 'Failed to connect account.');
    } finally {
      setConnectingAws(false);
    }
  }

  useEffect(() => {
    api.getAccounts().then(setAccounts).catch(console.error);
  }, []);

  useEffect(() => {
    if (activeSection === 'api-keys') {
      loadApiTokens();
    }
  }, [activeSection]);

  async function loadApiTokens() {
    setLoadingTokens(true);
    try {
      const data = await api.getAPITokens();
      setApiTokens(data.api_tokens || []);
    } catch (e) {
      console.error('Failed to load API tokens:', e);
    } finally {
      setLoadingTokens(false);
    }
  }

  async function handleCreateToken() {
    if (!newTokenName.trim()) return;
    try {
      const data = await api.createAPIToken({ name: newTokenName, scopes: newTokenScopes });
      setCreatedToken(data.token);
      setNewTokenName('');
      setShowCreateToken(false);
      loadApiTokens();
    } catch (e) {
      console.error('Failed to create token:', e);
    }
  }

  async function handleRevokeToken(tokenPrefix) {
    if (!confirm('Are you sure you want to revoke this API token? This cannot be undone.')) return;
    try {
      await api.revokeAPIToken(tokenPrefix);
      loadApiTokens();
    } catch (e) {
      console.error('Failed to revoke token:', e);
    }
  }

  function copyToken(text) {
    navigator.clipboard.writeText(text);
    setTokenCopied(true);
    setTimeout(() => setTokenCopied(false), 2000);
  }

  const sections = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'accounts', label: 'Integrations', icon: Plug },
    { id: 'api-keys', label: 'API Keys', icon: Key },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'appearance', label: 'Appearance', icon: Palette },
    { id: 'about', label: 'About', icon: Info },
  ];

  function copyToClipboard(text) {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="animate-fadeIn">
      <PageHeader title="Settings" description="Manage your account and preferences" icon={Settings} />

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Section nav */}
        <Card padding={false} className="lg:col-span-1 h-fit">
          <div className="p-2">
            {sections.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveSection(id)}
                className="w-full flex items-center gap-3 px-3 py-2.5 rounded-[var(--radius-md)] text-sm transition-all"
                style={{
                  backgroundColor: activeSection === id ? 'var(--brand-50)' : 'transparent',
                  color: activeSection === id ? 'var(--brand-700)' : 'var(--color-text-secondary)',
                  fontWeight: activeSection === id ? 600 : 400,
                }}
              >
                <Icon size={16} />
                {label}
              </button>
            ))}
          </div>
        </Card>

        {/* Content */}
        <div className="lg:col-span-3 space-y-6">
          {activeSection === 'profile' && (
            <Card>
              <CardTitle>Profile</CardTitle>
              <div className="space-y-4 mt-4">
                <div>
                  <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--color-text-secondary)' }}>Email</label>
                  <div
                    className="px-4 py-3 rounded-[var(--radius-md)] text-sm"
                    style={{ backgroundColor: 'var(--color-surface-secondary)', color: 'var(--color-text-primary)', border: '1px solid var(--color-border)' }}
                  >
                    {user?.email || 'Not available'}
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--color-text-secondary)' }}>Plan</label>
                  <div className="flex items-center gap-3">
                    <Badge variant="brand">Free Plan</Badge>
                    <span className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>
                      Upgrade to Pro for more features
                    </span>
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--color-text-secondary)' }}>Password</label>
                  <Button variant="secondary" size="sm" disabled>Change Password</Button>
                  <p className="text-xs mt-1" style={{ color: 'var(--color-text-tertiary)' }}>Coming soon</p>
                </div>
              </div>
            </Card>
          )}

          {activeSection === 'accounts' && (
            <Card>
              <CardTitle>Integrations</CardTitle>
              <p className="text-sm mt-3 mb-4" style={{ color: 'var(--color-text-secondary)' }}>
                Manage all your cloud and SaaS provider connections from the dedicated Integrations page.
              </p>
              <a href="/integrations">
                <Button size="sm" icon={Plug}>Go to Integrations</Button>
              </a>
              {accounts.length > 0 && (
                <div className="mt-6">
                  <p className="text-xs font-semibold uppercase tracking-wider mb-3" style={{ color: 'var(--color-text-tertiary)' }}>Legacy AWS Accounts</p>
                  <div className="space-y-2">
                    {accounts.map((acc) => (
                      <div
                        key={acc.id}
                        className="flex items-center justify-between p-3 rounded-[var(--radius-md)]"
                        style={{ backgroundColor: 'var(--color-surface-secondary)', border: '1px solid var(--color-border)' }}
                      >
                        <div>
                          <p className="text-sm font-medium" style={{ color: 'var(--color-text-primary)' }}>
                            {acc.account_name || 'AWS Account'}
                          </p>
                          <p className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>{acc.aws_account_id}</p>
                        </div>
                        <Badge variant="success">Connected</Badge>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </Card>
          )}

          {activeSection === 'api-keys' && (
            <Card>
              <div className="flex items-center justify-between mb-4">
                <CardTitle>API Keys</CardTitle>
                <Button size="sm" icon={Plus} onClick={() => { setShowCreateToken(true); setCreatedToken(null); }}>
                  Create Token
                </Button>
              </div>

              <p className="text-sm mb-4" style={{ color: 'var(--color-text-tertiary)' }}>
                API tokens authenticate requests to the CloudPulse v2 API. Tokens are shown only once at creation.
              </p>

              {/* Created token banner */}
              {createdToken && (
                <div
                  className="p-4 rounded-[var(--radius-md)] mb-4"
                  style={{ backgroundColor: 'var(--success-50)', border: '1px solid var(--success-200)' }}
                >
                  <div className="flex items-center gap-2 mb-2">
                    <Shield size={16} style={{ color: 'var(--success-600)' }} />
                    <span className="text-sm font-semibold" style={{ color: 'var(--success-700)' }}>Token created — copy it now!</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <code
                      className="flex-1 px-3 py-2 rounded-[var(--radius-sm)] text-xs font-mono"
                      style={{ backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)', color: 'var(--color-text-primary)', wordBreak: 'break-all' }}
                    >
                      {tokenVisible ? createdToken : createdToken.slice(0, 12) + '•'.repeat(32)}
                    </code>
                    <button
                      onClick={() => setTokenVisible(!tokenVisible)}
                      className="p-2 rounded-[var(--radius-sm)] transition-colors hover:bg-[var(--color-surface-secondary)]"
                      style={{ color: 'var(--color-text-tertiary)' }}
                      title={tokenVisible ? 'Hide' : 'Reveal'}
                    >
                      {tokenVisible ? <EyeOff size={14} /> : <Eye size={14} />}
                    </button>
                    <button
                      onClick={() => copyToken(createdToken)}
                      className="p-2 rounded-[var(--radius-sm)] transition-colors hover:bg-[var(--color-surface-secondary)]"
                      style={{ color: 'var(--color-text-tertiary)' }}
                      title="Copy token"
                    >
                      {tokenCopied ? <Check size={14} style={{ color: 'var(--success-600)' }} /> : <Copy size={14} />}
                    </button>
                  </div>
                </div>
              )}

              {/* Create form */}
              {showCreateToken && (
                <div
                  className="p-4 rounded-[var(--radius-md)] mb-4 space-y-3"
                  style={{ backgroundColor: 'var(--color-surface-secondary)', border: '1px solid var(--color-border)' }}
                >
                  <div>
                    <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--color-text-secondary)' }}>Name</label>
                    <input
                      type="text"
                      value={newTokenName}
                      onChange={(e) => setNewTokenName(e.target.value)}
                      placeholder="e.g., CI/CD Pipeline, Terraform"
                      className="w-full px-3 py-2 rounded-[var(--radius-md)] text-sm"
                      style={{ backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)', color: 'var(--color-text-primary)' }}
                      onKeyDown={(e) => e.key === 'Enter' && handleCreateToken()}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--color-text-secondary)' }}>Scopes</label>
                    <div className="flex gap-3">
                      {['read', 'read,write'].map((scope) => (
                        <button
                          key={scope}
                          onClick={() => setNewTokenScopes(scope)}
                          className="flex items-center gap-2 px-3 py-2 rounded-[var(--radius-md)] text-sm transition-all"
                          style={{
                            backgroundColor: newTokenScopes === scope ? 'var(--brand-50)' : 'var(--color-surface)',
                            border: `2px solid ${newTokenScopes === scope ? 'var(--brand-500)' : 'var(--color-border)'}`,
                            color: newTokenScopes === scope ? 'var(--brand-700)' : 'var(--color-text-secondary)',
                            fontWeight: newTokenScopes === scope ? 600 : 400,
                          }}
                        >
                          {scope === 'read' ? 'Read Only' : 'Read & Write'}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div className="flex gap-2 pt-1">
                    <Button size="sm" onClick={handleCreateToken} disabled={!newTokenName.trim()}>Create</Button>
                    <Button size="sm" variant="secondary" onClick={() => setShowCreateToken(false)}>Cancel</Button>
                  </div>
                </div>
              )}

              {/* Token list */}
              {loadingTokens ? (
                <p className="text-sm py-4" style={{ color: 'var(--color-text-tertiary)' }}>Loading tokens...</p>
              ) : apiTokens.length === 0 ? (
                <p className="text-sm py-4" style={{ color: 'var(--color-text-tertiary)' }}>
                  No API tokens yet. Create one to authenticate with the v2 API.
                </p>
              ) : (
                <div className="space-y-2">
                  {apiTokens.map((t) => (
                    <div
                      key={t.token_prefix}
                      className="flex items-center justify-between p-4 rounded-[var(--radius-md)]"
                      style={{ backgroundColor: 'var(--color-surface-secondary)', border: '1px solid var(--color-border)' }}
                    >
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-medium truncate" style={{ color: 'var(--color-text-primary)' }}>{t.name}</p>
                          <Badge variant={t.scopes?.includes('write') ? 'warning' : 'brand'}>
                            {t.scopes?.includes('write') ? 'read/write' : 'read'}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-3 mt-1">
                          <code className="text-xs font-mono" style={{ color: 'var(--color-text-tertiary)' }}>
                            {t.token_prefix}•••
                          </code>
                          <span className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>
                            Created {new Date(t.created_at).toLocaleDateString()}
                          </span>
                          {t.last_used_at && (
                            <span className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>
                              Last used {new Date(t.last_used_at).toLocaleDateString()}
                            </span>
                          )}
                        </div>
                      </div>
                      <button
                        onClick={() => handleRevokeToken(t.token_prefix)}
                        className="p-2 rounded-[var(--radius-sm)] transition-colors hover:bg-[var(--color-surface)]"
                        style={{ color: 'var(--color-text-tertiary)' }}
                        title="Revoke token"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          )}

          {activeSection === 'notifications' && (
            <Card>
              <CardTitle>Notifications</CardTitle>
              <div className="space-y-4 mt-4">
                <div className="flex items-center justify-between p-4 rounded-[var(--radius-md)]" style={{ backgroundColor: 'var(--color-surface-secondary)' }}>
                  <div>
                    <p className="text-sm font-medium" style={{ color: 'var(--color-text-primary)' }}>Email Alerts</p>
                    <p className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>Receive alerts for anomalies and budget warnings</p>
                  </div>
                  <Badge variant="success">Active</Badge>
                </div>
                <div className="flex items-center justify-between p-4 rounded-[var(--radius-md)]" style={{ backgroundColor: 'var(--color-surface-secondary)' }}>
                  <div>
                    <p className="text-sm font-medium" style={{ color: 'var(--color-text-primary)' }}>Daily Digest</p>
                    <p className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>Get a daily summary of your cloud spending</p>
                  </div>
                  <Badge variant="neutral">Coming Soon</Badge>
                </div>
                <div className="flex items-center justify-between p-4 rounded-[var(--radius-md)]" style={{ backgroundColor: 'var(--color-surface-secondary)' }}>
                  <div>
                    <p className="text-sm font-medium" style={{ color: 'var(--color-text-primary)' }}>Slack Integration</p>
                    <p className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>Send alerts to a Slack channel</p>
                  </div>
                  <Badge variant="neutral">Coming Soon</Badge>
                </div>
              </div>
            </Card>
          )}

          {activeSection === 'appearance' && (
            <Card>
              <CardTitle>Appearance</CardTitle>
              <div className="mt-4">
                <label className="block text-sm font-medium mb-3" style={{ color: 'var(--color-text-secondary)' }}>Theme</label>
                <div className="flex gap-3">
                  {[
                    { value: 'light', label: 'Light', emoji: '☀️' },
                    { value: 'dark', label: 'Dark', emoji: '🌙' },
                  ].map((opt) => (
                    <button
                      key={opt.value}
                      onClick={() => setTheme(opt.value)}
                      className="flex items-center gap-2 px-4 py-3 rounded-[var(--radius-md)] text-sm font-medium transition-all"
                      style={{
                        backgroundColor: theme === opt.value ? 'var(--brand-50)' : 'var(--color-surface-secondary)',
                        border: `2px solid ${theme === opt.value ? 'var(--brand-500)' : 'var(--color-border)'}`,
                        color: theme === opt.value ? 'var(--brand-700)' : 'var(--color-text-secondary)',
                      }}
                    >
                      <span>{opt.emoji}</span>
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>
            </Card>
          )}

          {activeSection === 'about' && (
            <Card>
              <CardTitle>About CloudPulse</CardTitle>
              <div className="space-y-3 mt-4">
                <div className="flex justify-between text-sm">
                  <span style={{ color: 'var(--color-text-secondary)' }}>Version</span>
                  <span className="font-medium" style={{ color: 'var(--color-text-primary)' }}>0.1.0</span>
                </div>
                <div className="flex justify-between text-sm" style={{ borderTop: '1px solid var(--color-border)', paddingTop: '12px' }}>
                  <span style={{ color: 'var(--color-text-secondary)' }}>Stack</span>
                  <span className="font-medium" style={{ color: 'var(--color-text-primary)' }}>React + FastAPI + PostgreSQL</span>
                </div>
                <div className="flex justify-between text-sm" style={{ borderTop: '1px solid var(--color-border)', paddingTop: '12px' }}>
                  <span style={{ color: 'var(--color-text-secondary)' }}>Target Pricing</span>
                  <span className="font-medium" style={{ color: 'var(--color-text-primary)' }}>$29-49/mo</span>
                </div>
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
