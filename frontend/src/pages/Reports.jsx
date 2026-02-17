import { useEffect, useState } from 'react';
import { FileText, Copy, Check, ExternalLink, Plus } from 'lucide-react';
import { api } from '../api/client';
import { Card, CardTitle } from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { EmptyState } from '../components/ui/EmptyState';
import { SkeletonCard, Skeleton } from '../components/ui/Skeleton';

export default function Reports() {
  const [reports, setReports] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [copiedId, setCopiedId] = useState(null);

  useEffect(() => {
    async function load() {
      try {
        const accts = await api.getAccounts();
        setAccounts(accts);
        if (accts.length > 0) {
          const data = await api.getSharedReports(accts[0].id).catch(() => []);
          setReports(data);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  async function handleCreate() {
    if (accounts.length === 0) return;
    setCreating(true);
    try {
      const report = await api.createSharedReport(accounts[0].id);
      setReports([report, ...reports]);
    } catch (err) {
      console.error(err);
    } finally {
      setCreating(false);
    }
  }

  function copyLink(report) {
    const url = `${window.location.origin}/api/v1/reports/${report.token || report.id}`;
    navigator.clipboard.writeText(url);
    setCopiedId(report.id);
    setTimeout(() => setCopiedId(null), 2000);
  }

  if (loading) {
    return (
      <div className="animate-fadeIn">
        <div className="flex items-center justify-between mb-8">
          <div><Skeleton variant="text" className="w-32 h-7 mb-2" /><Skeleton variant="text" className="w-56 h-4" /></div>
        </div>
        <div className="space-y-4 stagger-children"><SkeletonCard /><SkeletonCard /></div>
      </div>
    );
  }

  return (
    <div className="animate-fadeIn">
      <PageHeader title="Shared Reports" description="Create shareable cost report links for stakeholders" icon={FileText}>
        <Button size="sm" icon={Plus} onClick={handleCreate} loading={creating}>New Report</Button>
      </PageHeader>

      {reports.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="No shared reports"
          description="Create a shareable report to send cost summaries to managers or finance teams — no login required."
          actionLabel="Create Report"
          actionIcon={Plus}
          onAction={handleCreate}
        />
      ) : (
        <div className="space-y-4 stagger-children">
          {reports.map((report) => (
            <Card key={report.id}>
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="text-sm font-semibold" style={{ color: 'var(--color-text-primary)' }}>
                      Cost Report
                    </h3>
                    <Badge variant="info">Public Link</Badge>
                  </div>
                  <p className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>
                    Created: {new Date(report.created_at).toLocaleDateString()} · 
                    {report.expires_at ? ` Expires: ${new Date(report.expires_at).toLocaleDateString()}` : ' No expiry'}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="secondary"
                    size="sm"
                    icon={copiedId === report.id ? Check : Copy}
                    onClick={() => copyLink(report)}
                  >
                    {copiedId === report.id ? 'Copied!' : 'Copy Link'}
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    icon={ExternalLink}
                    onClick={() => window.open(`/api/v1/reports/${report.token || report.id}`, '_blank')}
                  >
                    Open
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
