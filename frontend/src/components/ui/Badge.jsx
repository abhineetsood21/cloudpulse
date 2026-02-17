const variantStyles = {
  success: { background: 'var(--color-success-bg)', color: 'var(--color-success-text)' },
  warning: { background: 'var(--color-warning-bg)', color: 'var(--color-warning-text)' },
  error: { background: 'var(--color-error-bg)', color: 'var(--color-error-text)' },
  info: { background: 'var(--color-info-bg)', color: 'var(--color-info-text)' },
  neutral: { background: 'var(--color-surface-secondary)', color: 'var(--color-text-secondary)' },
  brand: { background: 'var(--brand-50)', color: 'var(--brand-700)' },
};

export function Badge({
  children,
  variant = 'neutral',
  icon: Icon,
  size = 'sm',
  className = '',
}) {
  const sizeClasses = size === 'sm'
    ? 'px-2 py-0.5 text-xs'
    : 'px-2.5 py-1 text-sm';

  return (
    <span
      className={`inline-flex items-center gap-1 font-semibold rounded-full ${sizeClasses} ${className}`}
      style={variantStyles[variant] || variantStyles.neutral}
    >
      {Icon && <Icon size={size === 'sm' ? 12 : 14} />}
      {children}
    </span>
  );
}
