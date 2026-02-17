export function PageHeader({ title, description, icon: Icon, children, className = '' }) {
  return (
    <div className={`flex items-center justify-between mb-8 animate-fadeIn ${className}`}>
      <div>
        <h1
          className="text-2xl font-bold flex items-center gap-2.5"
          style={{ color: 'var(--color-text-primary)' }}
        >
          {Icon && (
            <div
              className="p-2 rounded-[var(--radius-md)]"
              style={{ background: 'var(--brand-50)', color: 'var(--brand-600)' }}
            >
              <Icon size={20} />
            </div>
          )}
          {title}
        </h1>
        {description && (
          <p
            className="mt-1.5 text-sm"
            style={{ color: 'var(--color-text-secondary)', marginLeft: Icon ? '42px' : 0 }}
          >
            {description}
          </p>
        )}
      </div>
      {children && (
        <div className="flex items-center gap-2">
          {children}
        </div>
      )}
    </div>
  );
}
