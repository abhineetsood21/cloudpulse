import { TrendingUp, TrendingDown } from 'lucide-react';

export function StatCard({
  icon: Icon,
  label,
  value,
  trend,
  trendLabel,
  className = '',
}) {
  return (
    <div
      className={`rounded-[var(--radius-lg)] p-5 transition-all duration-200 hover:shadow-[var(--shadow-md)] ${className}`}
      style={{
        backgroundColor: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        boxShadow: 'var(--shadow-sm)',
      }}
    >
      <div className="flex items-start justify-between mb-3">
        {Icon && (
          <div
            className="p-2.5 rounded-[var(--radius-md)]"
            style={{ background: 'var(--brand-50)', color: 'var(--brand-600)' }}
          >
            <Icon size={18} />
          </div>
        )}
        {trend !== undefined && trend !== null && (
          <div
            className="flex items-center gap-1 text-xs font-semibold px-2 py-1 rounded-full"
            style={{
              background: trend >= 0 ? 'var(--color-error-bg)' : 'var(--color-success-bg)',
              color: trend >= 0 ? 'var(--color-error-text)' : 'var(--color-success-text)',
            }}
          >
            {trend >= 0 ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
            {Math.abs(trend).toFixed(1)}%
          </div>
        )}
      </div>
      <p className="text-sm mb-1" style={{ color: 'var(--color-text-secondary)' }}>
        {label}
      </p>
      <p className="text-2xl font-bold" style={{ color: 'var(--color-text-primary)' }}>
        {value}
      </p>
      {trendLabel && (
        <p className="text-xs mt-1" style={{ color: 'var(--color-text-tertiary)' }}>
          {trendLabel}
        </p>
      )}
    </div>
  );
}
