import { Loader2 } from 'lucide-react';

const variants = {
  primary: `text-white font-medium`,
  secondary: `font-medium`,
  ghost: `font-medium`,
  danger: `text-white font-medium`,
};

const sizes = {
  sm: 'px-3 py-1.5 text-xs gap-1.5',
  md: 'px-4 py-2.5 text-sm gap-2',
  lg: 'px-6 py-3 text-base gap-2.5',
};

export function Button({
  children,
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  icon: Icon,
  className = '',
  ...props
}) {
  const getStyle = () => {
    const base = {
      borderRadius: 'var(--radius-md)',
      transition: 'all 0.15s ease',
    };
    switch (variant) {
      case 'primary':
        return { ...base, background: 'var(--brand-600)', border: 'none' };
      case 'secondary':
        return { ...base, background: 'var(--color-surface)', border: '1px solid var(--color-border)', color: 'var(--color-text-primary)' };
      case 'ghost':
        return { ...base, background: 'transparent', border: 'none', color: 'var(--color-text-secondary)' };
      case 'danger':
        return { ...base, background: 'var(--color-error)', border: 'none' };
      default:
        return base;
    }
  };

  return (
    <button
      className={`
        inline-flex items-center justify-center
        ${variants[variant]}
        ${sizes[size]}
        disabled:opacity-50 disabled:cursor-not-allowed
        ${variant === 'primary' ? 'hover:opacity-90' : ''}
        ${variant === 'secondary' ? 'hover:bg-[var(--color-surface-hover)]' : ''}
        ${variant === 'ghost' ? 'hover:bg-[var(--color-surface-secondary)]' : ''}
        ${variant === 'danger' ? 'hover:opacity-90' : ''}
        ${className}
      `}
      style={getStyle()}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <Loader2 size={size === 'sm' ? 14 : 16} className="animate-spin" />
      ) : Icon ? (
        <Icon size={size === 'sm' ? 14 : 16} />
      ) : null}
      {children}
    </button>
  );
}
