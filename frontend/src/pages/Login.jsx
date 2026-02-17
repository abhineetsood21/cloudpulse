import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { DollarSign, TrendingUp, Shield, Zap, BarChart3, Bell, Eye, EyeOff } from 'lucide-react';

const features = [
  { icon: DollarSign, title: 'Cost Monitoring', desc: 'Track AWS spending across all services in real-time' },
  { icon: TrendingUp, title: 'AI-Powered Insights', desc: 'Plain-English explanations of cost changes' },
  { icon: Bell, title: 'Budget Alerts', desc: 'Get notified before you overspend' },
  { icon: BarChart3, title: 'Cost Forecasting', desc: 'Predict end-of-month spend accurately' },
  { icon: Shield, title: '5-Minute Setup', desc: 'One-click CloudFormation — no credentials stored' },
  { icon: Zap, title: 'Savings Engine', desc: 'Find idle resources and save up to 40%' },
];

function PasswordStrength({ password }) {
  const getStrength = () => {
    if (!password) return 0;
    let score = 0;
    if (password.length >= 8) score++;
    if (/[A-Z]/.test(password)) score++;
    if (/[0-9]/.test(password)) score++;
    if (/[^A-Za-z0-9]/.test(password)) score++;
    return score;
  };
  const strength = getStrength();
  const labels = ['', 'Weak', 'Fair', 'Good', 'Strong'];
  const colors = ['', 'var(--color-error)', 'var(--color-warning)', 'var(--color-info)', 'var(--color-success)'];

  if (!password) return null;
  return (
    <div className="mt-2">
      <div className="flex gap-1">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="h-1 flex-1 rounded-full transition-all duration-300"
            style={{ backgroundColor: i <= strength ? colors[strength] : 'var(--color-border)' }}
          />
        ))}
      </div>
      <p className="text-xs mt-1" style={{ color: colors[strength] }}>{labels[strength]}</p>
    </div>
  );
}

export default function Login() {
  const { login, signup } = useAuth();
  const [isSignup, setIsSignup] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (isSignup) {
        await signup(email, password);
      } else {
        await login(email, password);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex" style={{ backgroundColor: 'var(--color-bg)' }}>
      {/* Left panel — feature showcase */}
      <div
        className="hidden lg:flex lg:w-[55%] relative overflow-hidden flex-col justify-between p-12"
        style={{ background: 'linear-gradient(135deg, #312e81, #4f46e5, #6366f1, #7c3aed)' }}
      >
        {/* Decorative shapes */}
        <div className="absolute top-0 right-0 w-96 h-96 rounded-full opacity-10" style={{ background: 'white', transform: 'translate(30%, -30%)' }} />
        <div className="absolute bottom-0 left-0 w-72 h-72 rounded-full opacity-10" style={{ background: 'white', transform: 'translate(-30%, 30%)' }} />
        <div className="absolute top-1/2 left-1/2 w-64 h-64 rounded-full opacity-5" style={{ background: 'white', transform: 'translate(-50%, -50%)' }} />

        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-xl bg-white/20 flex items-center justify-center">
              <span className="text-xl">⚡</span>
            </div>
            <span className="text-white text-2xl font-bold tracking-tight">CloudPulse</span>
          </div>
          <p className="text-indigo-200 text-sm">AWS Cost Monitoring for Modern Teams</p>
        </div>

        <div className="relative z-10">
          <h2 className="text-white text-3xl font-bold leading-tight mb-3">
            Stop overpaying<br />for AWS.
          </h2>
          <p className="text-indigo-200 text-lg mb-10 max-w-md">
            Join teams saving thousands monthly with AI-powered cost intelligence. Set up in 5 minutes.
          </p>

          <div className="grid grid-cols-2 gap-4">
            {features.map(({ icon: Icon, title, desc }) => (
              <div key={title} className="bg-white/10 rounded-xl p-4 backdrop-blur-sm">
                <Icon size={20} className="text-indigo-200 mb-2" />
                <h3 className="text-white font-semibold text-sm mb-1">{title}</h3>
                <p className="text-indigo-300 text-xs leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="relative z-10">
          <p className="text-indigo-300 text-sm">
            Starting at <span className="text-white font-semibold">$29/mo</span> — 10x cheaper than enterprise tools
          </p>
        </div>
      </div>

      {/* Right panel — auth form */}
      <div className="flex-1 flex items-center justify-center p-6 lg:p-12">
        <div className="w-full max-w-md animate-fadeInUp">
          {/* Mobile logo */}
          <div className="lg:hidden text-center mb-8">
            <div className="flex items-center justify-center gap-2 mb-2">
              <div className="w-10 h-10 rounded-xl gradient-brand flex items-center justify-center">
                <span className="text-xl">⚡</span>
              </div>
              <span className="text-2xl font-bold text-gradient">CloudPulse</span>
            </div>
            <p className="text-sm" style={{ color: 'var(--color-text-tertiary)' }}>AWS Cost Monitoring</p>
          </div>

          <div className="mb-8">
            <h2 className="text-2xl font-bold mb-2" style={{ color: 'var(--color-text-primary)' }}>
              {isSignup ? 'Create your account' : 'Welcome back'}
            </h2>
            <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
              {isSignup ? 'Start monitoring your AWS costs in minutes' : 'Sign in to your CloudPulse dashboard'}
            </p>
          </div>

          <form onSubmit={handleSubmit}>
            {error && (
              <div
                className="rounded-[var(--radius-md)] px-4 py-3 mb-5 text-sm animate-fadeIn"
                style={{ backgroundColor: 'var(--color-error-bg)', color: 'var(--color-error-text)', border: '1px solid var(--color-error)' }}
              >
                {error}
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--color-text-primary)' }}>Email</label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-4 py-3 rounded-[var(--radius-md)] text-sm outline-none transition-all duration-150"
                  style={{
                    backgroundColor: 'var(--color-surface)',
                    border: '1px solid var(--color-border)',
                    color: 'var(--color-text-primary)',
                  }}
                  onFocus={(e) => e.target.style.borderColor = 'var(--color-border-focus)'}
                  onBlur={(e) => e.target.style.borderColor = 'var(--color-border)'}
                  placeholder="you@company.com"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--color-text-primary)' }}>Password</label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    required
                    minLength={8}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-4 py-3 pr-11 rounded-[var(--radius-md)] text-sm outline-none transition-all duration-150"
                    style={{
                      backgroundColor: 'var(--color-surface)',
                      border: '1px solid var(--color-border)',
                      color: 'var(--color-text-primary)',
                    }}
                    onFocus={(e) => e.target.style.borderColor = 'var(--color-border-focus)'}
                    onBlur={(e) => e.target.style.borderColor = 'var(--color-border)'}
                    placeholder="Min 8 characters"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 p-1"
                    style={{ color: 'var(--color-text-tertiary)' }}
                    tabIndex={-1}
                  >
                    {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
                {isSignup && <PasswordStrength password={password} />}
              </div>
            </div>

            {!isSignup && (
              <div className="flex justify-end mt-2">
                <button type="button" className="text-xs font-medium" style={{ color: 'var(--brand-600)' }}>
                  Forgot password?
                </button>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full mt-6 px-4 py-3 text-white rounded-[var(--radius-md)] text-sm font-semibold transition-all duration-150 disabled:opacity-50 hover:opacity-90"
              style={{ background: 'var(--brand-600)' }}
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Please wait...
                </span>
              ) : isSignup ? 'Create Account' : 'Sign In'}
            </button>

            <p className="text-center text-sm mt-6" style={{ color: 'var(--color-text-secondary)' }}>
              {isSignup ? 'Already have an account?' : "Don't have an account?"}{' '}
              <button
                type="button"
                onClick={() => { setIsSignup(!isSignup); setError(''); }}
                className="font-semibold hover:underline"
                style={{ color: 'var(--brand-600)' }}
              >
                {isSignup ? 'Sign In' : 'Sign Up'}
              </button>
            </p>
          </form>
        </div>
      </div>
    </div>
  );
}
