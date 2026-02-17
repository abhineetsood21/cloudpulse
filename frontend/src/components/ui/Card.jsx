export function Card({ children, className = '', hover = false, padding = true, ...props }) {
  return (
    <div
      className={`
        rounded-[var(--radius-lg)] transition-all duration-200
        ${hover ? 'hover:shadow-[var(--shadow-md)] hover:translate-y-[-1px] cursor-pointer' : ''}
        ${padding ? 'p-6' : ''}
        ${className}
      `}
      style={{
        backgroundColor: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        boxShadow: 'var(--shadow-sm)',
      }}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardHeader({ children, className = '' }) {
  return (
    <div className={`flex items-center justify-between mb-4 ${className}`}>
      {children}
    </div>
  );
}

export function CardTitle({ children, className = '' }) {
  return (
    <h3 className={`text-lg font-semibold ${className}`} style={{ color: 'var(--color-text-primary)' }}>
      {children}
    </h3>
  );
}
