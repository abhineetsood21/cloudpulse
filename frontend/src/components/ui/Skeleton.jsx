export function Skeleton({ className = '', variant = 'rect', ...props }) {
  const base = 'animate-shimmer rounded-[var(--radius-md)]';

  if (variant === 'circle') {
    return <div className={`${base} rounded-full ${className}`} {...props} />;
  }

  if (variant === 'text') {
    return <div className={`${base} h-4 ${className}`} {...props} />;
  }

  return <div className={`${base} ${className}`} {...props} />;
}

export function SkeletonCard({ className = '' }) {
  return (
    <div
      className={`rounded-[var(--radius-lg)] p-6 ${className}`}
      style={{ backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)' }}
    >
      <div className="flex items-center gap-3 mb-4">
        <Skeleton variant="circle" className="w-10 h-10" />
        <div className="flex-1 space-y-2">
          <Skeleton variant="text" className="w-24" />
          <Skeleton variant="text" className="w-32 h-6" />
        </div>
      </div>
    </div>
  );
}

export function SkeletonChart({ className = '' }) {
  return (
    <div
      className={`rounded-[var(--radius-lg)] p-6 ${className}`}
      style={{ backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)' }}
    >
      <Skeleton variant="text" className="w-40 h-5 mb-4" />
      <div className="flex items-end gap-2 h-48">
        {[40, 65, 45, 80, 55, 70, 50, 85, 60, 75, 45, 90].map((h, i) => (
          <Skeleton key={i} className="flex-1" style={{ height: `${h}%` }} />
        ))}
      </div>
    </div>
  );
}

export function SkeletonTable({ rows = 5, cols = 4, className = '' }) {
  return (
    <div
      className={`rounded-[var(--radius-lg)] p-6 ${className}`}
      style={{ backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)' }}
    >
      <Skeleton variant="text" className="w-40 h-5 mb-6" />
      <div className="space-y-4">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="flex gap-4">
            {Array.from({ length: cols }).map((_, j) => (
              <Skeleton
                key={j}
                variant="text"
                className={j === 0 ? 'flex-2 h-4' : 'flex-1 h-4'}
                style={{ opacity: 1 - i * 0.1 }}
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
