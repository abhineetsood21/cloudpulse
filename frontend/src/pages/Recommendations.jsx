import { useState, useEffect } from 'react';
import { Lightbulb, DollarSign, CheckCircle2, Clock, ArrowUpRight, Filter, TrendingDown } from 'lucide-react';
import { api } from '../api/client';
import { Card, CardTitle } from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';

const CATEGORY_ICONS = {
  rightsizing: TrendingDown,
  unused: Clock,
  purchase: DollarSign,
};

export default function Recommendations() {
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showResolved, setShowResolved] = useState(false);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    loadRecommendations();
  }, [showResolved]);

  async function loadRecommendations() {
    setLoading(true);
    try {
      const accounts = await api.getAccounts();
      if (accounts.length > 0) {
        const data = await api.getRecommendations(accounts[0].id, showResolved);
        setRecommendations(data || []);
      }
    } catch (e) {
      console.error('Failed to load recommendations:', e);
    } finally {
      setLoading(false);
    }
  }

  async function handleResolve(id) {
    try {
      await api.resolveRecommendation(id);
      loadRecommendations();
    } catch (e) {
      console.error('Failed to resolve:', e);
    }
  }

  const filtered = filter === 'all'
    ? recommendations
    : recommendations.filter((r) => r.resource_type === filter);

  const totalSavings = filtered
    .filter((r) => !r.is_resolved)
    .reduce((sum, r) => sum + (r.estimated_monthly_savings || 0), 0);

  return (
    <div className="animate-fadeIn">
      <PageHeader
        title="Recommendations"
        description="Cost optimization opportunities across your AWS accounts"
        icon={Lightbulb}
      />

      {/* Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium" style={{ color: 'var(--color-text-tertiary)' }}>Total Savings</p>
              <p className="text-2xl font-bold mt-1" style={{ color: 'var(--success-600)' }}>
                ${totalSavings.toFixed(0)}<span className="text-sm font-normal">/mo</span>
              </p>
            </div>
            <div className="p-2.5 rounded-lg" style={{ backgroundColor: 'var(--success-50)' }}>
              <DollarSign size={20} style={{ color: 'var(--success-600)' }} />
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium" style={{ color: 'var(--color-text-tertiary)' }}>Open</p>
              <p className="text-2xl font-bold mt-1" style={{ color: 'var(--color-text-primary)' }}>
                {filtered.filter((r) => !r.is_resolved).length}
              </p>
            </div>
            <div className="p-2.5 rounded-lg" style={{ backgroundColor: 'var(--brand-50)' }}>
              <Lightbulb size={20} style={{ color: 'var(--brand-600)' }} />
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium" style={{ color: 'var(--color-text-tertiary)' }}>Resolved</p>
              <p className="text-2xl font-bold mt-1" style={{ color: 'var(--color-text-primary)' }}>
                {filtered.filter((r) => r.is_resolved).length}
              </p>
            </div>
            <div className="p-2.5 rounded-lg" style={{ backgroundColor: 'var(--color-surface-secondary)' }}>
              <CheckCircle2 size={20} style={{ color: 'var(--success-600)' }} />
            </div>
          </div>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 mb-4">
        <Button
          size="sm"
          variant={showResolved ? 'primary' : 'secondary'}
          onClick={() => setShowResolved(!showResolved)}
        >
          {showResolved ? 'Hide Resolved' : 'Show Resolved'}
        </Button>
      </div>

      {/* List */}
      {loading ? (
        <Card>
          <p className="text-sm py-8 text-center" style={{ color: 'var(--color-text-tertiary)' }}>
            Loading recommendations...
          </p>
        </Card>
      ) : filtered.length === 0 ? (
        <Card>
          <div className="text-center py-12">
            <CheckCircle2 size={40} className="mx-auto mb-3" style={{ color: 'var(--success-500)' }} />
            <p className="text-sm font-medium" style={{ color: 'var(--color-text-primary)' }}>
              No recommendations found
            </p>
            <p className="text-xs mt-1" style={{ color: 'var(--color-text-tertiary)' }}>
              Your infrastructure looks well-optimized!
            </p>
          </div>
        </Card>
      ) : (
        <div className="space-y-3">
          {filtered.map((rec) => (
            <Card key={rec.id}>
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <p className="text-sm font-medium" style={{ color: 'var(--color-text-primary)' }}>
                      {rec.recommendation}
                    </p>
                    {rec.is_resolved && <Badge variant="success">Resolved</Badge>}
                  </div>
                  <div className="flex items-center gap-3 text-xs" style={{ color: 'var(--color-text-tertiary)' }}>
                    <span>{rec.resource_type}</span>
                    <span>{rec.resource_id}</span>
                    <span>{rec.region}</span>
                  </div>
                </div>
                <div className="flex items-center gap-3 ml-4">
                  <div className="text-right">
                    <p className="text-sm font-semibold" style={{ color: 'var(--success-600)' }}>
                      ${rec.estimated_monthly_savings?.toFixed(0)}/mo
                    </p>
                  </div>
                  {!rec.is_resolved && (
                    <Button size="sm" variant="secondary" onClick={() => handleResolve(rec.id)}>
                      Resolve
                    </Button>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
