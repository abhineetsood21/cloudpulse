import { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { Tag, Search } from 'lucide-react';
import { api } from '../api/client';
import { Card, CardTitle } from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';
import { EmptyState } from '../components/ui/EmptyState';
import { SkeletonChart, SkeletonTable, Skeleton } from '../components/ui/Skeleton';

const chartTooltipStyle = {
  backgroundColor: 'var(--color-surface-elevated)',
  border: '1px solid var(--color-border)',
  borderRadius: 'var(--radius-md)',
  boxShadow: 'var(--shadow-md)',
  color: 'var(--color-text-primary)',
};

export default function Tags() {
  const [tags, setTags] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTag, setSelectedTag] = useState(null);
  const [tagCosts, setTagCosts] = useState(null);
  const [search, setSearch] = useState('');

  useEffect(() => {
    async function load() {
      try {
        const accts = await api.getAccounts();
        setAccounts(accts);
        if (accts.length > 0) {
          const data = await api.getAvailableTags(accts[0].id);
          setTags(data.tags || data || []);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  useEffect(() => {
    if (!selectedTag || accounts.length === 0) return;
    async function loadTagCosts() {
      try {
        const data = await api.getCostsByTag(accounts[0].id, selectedTag);
        setTagCosts(data);
      } catch (err) {
        console.error(err);
        setTagCosts(null);
      }
    }
    loadTagCosts();
  }, [selectedTag, accounts]);

  if (loading) {
    return (
      <div className="animate-fadeIn">
        <div className="flex items-center justify-between mb-8">
          <div><Skeleton variant="text" className="w-40 h-7 mb-2" /><Skeleton variant="text" className="w-56 h-4" /></div>
        </div>
        <SkeletonChart className="mb-6" />
        <SkeletonTable rows={5} cols={3} />
      </div>
    );
  }

  const filteredTags = tags.filter((t) => t.toLowerCase().includes(search.toLowerCase()));

  const chartData = tagCosts?.breakdown?.slice(0, 10).map((item) => ({
    name: item.value || '(untagged)',
    amount: item.amount,
  })) || [];

  return (
    <div className="animate-fadeIn">
      <PageHeader title="Tag Breakdown" description="View costs grouped by resource tags across providers" icon={Tag} />

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Tag list */}
        <Card className="lg:col-span-1" padding={false}>
          <div className="p-4" style={{ borderBottom: '1px solid var(--color-border)' }}>
            <div className="relative">
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: 'var(--color-text-tertiary)' }} />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Filter tags..."
                className="w-full pl-8 pr-3 py-2 rounded-[var(--radius-md)] text-sm outline-none"
                style={{ backgroundColor: 'var(--color-surface-secondary)', border: '1px solid var(--color-border)', color: 'var(--color-text-primary)' }}
              />
            </div>
          </div>
          <div className="max-h-96 overflow-y-auto p-2">
            {filteredTags.length === 0 ? (
              <p className="text-sm text-center py-8" style={{ color: 'var(--color-text-tertiary)' }}>No tags found</p>
            ) : (
              filteredTags.map((tag) => (
                <button
                  key={tag}
                  onClick={() => setSelectedTag(tag)}
                  className="w-full text-left px-3 py-2 rounded-[var(--radius-sm)] text-sm transition-all"
                  style={{
                    backgroundColor: selectedTag === tag ? 'var(--brand-50)' : 'transparent',
                    color: selectedTag === tag ? 'var(--brand-700)' : 'var(--color-text-secondary)',
                    fontWeight: selectedTag === tag ? 600 : 400,
                  }}
                >
                  {tag}
                </button>
              ))
            )}
          </div>
        </Card>

        {/* Cost breakdown */}
        <div className="lg:col-span-3 space-y-6">
          {!selectedTag ? (
            <EmptyState
              icon={Tag}
              title="Select a tag"
              description="Choose a tag from the list to see cost breakdown by tag values."
            />
          ) : tagCosts ? (
            <>
              <Card>
                <CardTitle>Cost by {selectedTag}</CardTitle>
                {chartData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={chartData} layout="vertical" margin={{ left: 100, right: 20 }}>
                      <XAxis type="number" tickFormatter={(v) => `$${v.toFixed(0)}`} tick={{ fontSize: 11, fill: 'var(--color-text-tertiary)' }} axisLine={false} tickLine={false} />
                      <YAxis type="category" dataKey="name" width={90} tick={{ fontSize: 11, fill: 'var(--color-text-secondary)' }} axisLine={false} tickLine={false} />
                      <Tooltip contentStyle={chartTooltipStyle} formatter={(value) => [`$${value.toFixed(2)}`, 'Cost']} />
                      <Bar dataKey="amount" fill="var(--chart-1)" radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <p className="text-sm py-8 text-center" style={{ color: 'var(--color-text-tertiary)' }}>No data for this tag</p>
                )}
              </Card>

              {tagCosts.breakdown && tagCosts.breakdown.length > 0 && (
                <Card>
                  <CardTitle>Details</CardTitle>
                  <table className="w-full">
                    <thead>
                      <tr className="text-left text-xs uppercase tracking-wider" style={{ color: 'var(--color-text-tertiary)', borderBottom: '1px solid var(--color-border)' }}>
                        <th className="pb-3 font-semibold">Tag Value</th>
                        <th className="pb-3 font-semibold text-right">Amount</th>
                        <th className="pb-3 font-semibold text-right">% of Total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {tagCosts.breakdown.map((item, i) => {
                        const total = tagCosts.breakdown.reduce((s, b) => s + b.amount, 0);
                        const pct = total > 0 ? (item.amount / total * 100) : 0;
                        return (
                          <tr key={i} style={{ borderBottom: '1px solid var(--color-border-light)' }}>
                            <td className="py-3 text-sm" style={{ color: 'var(--color-text-primary)' }}>{item.value || '(untagged)'}</td>
                            <td className="py-3 text-sm text-right font-semibold" style={{ color: 'var(--color-text-primary)' }}>${item.amount.toFixed(2)}</td>
                            <td className="py-3 text-sm text-right" style={{ color: 'var(--color-text-secondary)' }}>{pct.toFixed(1)}%</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </Card>
              )}
            </>
          ) : (
            <Card>
              <div className="flex items-center justify-center py-12">
                <div className="w-6 h-6 border-2 border-t-transparent rounded-full animate-spin" style={{ borderColor: 'var(--brand-500)', borderTopColor: 'transparent' }} />
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
