import { Button } from './Button';

export function EmptyState({
  icon: Icon,
  title,
  description,
  actionLabel,
  actionIcon,
  onAction,
  className = '',
}) {
  return (
    <div
      className={`rounded-[var(--radius-lg)] p-16 text-center animate-fadeIn ${className}`}
      style={{
        backgroundColor: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
      }}
    >
      {Icon && (
        <div
          className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-5"
          style={{ backgroundColor: 'var(--color-surface-secondary)' }}
        >
          <Icon size={28} style={{ color: 'var(--color-text-tertiary)' }} />
        </div>
      )}
      <h3
        className="text-lg font-semibold mb-2"
        style={{ color: 'var(--color-text-primary)' }}
      >
        {title}
      </h3>
      {description && (
        <p
          className="text-sm max-w-sm mx-auto mb-6"
          style={{ color: 'var(--color-text-secondary)' }}
        >
          {description}
        </p>
      )}
      {actionLabel && onAction && (
        <Button onClick={onAction} icon={actionIcon}>
          {actionLabel}
        </Button>
      )}
    </div>
  );
}
