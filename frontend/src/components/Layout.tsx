import { useState, useEffect } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import {
  Home, LayoutDashboard, Sparkles, BarChart3,
  Settings as Cog, Menu, X,
} from 'lucide-react';
import DemoBanner from './DemoBanner';

const nav = [
  { to: '/', label: 'Home', icon: Home, end: true },
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/suggestions', label: 'Suggestions', icon: Sparkles },
  { to: '/polls', label: 'Polls', icon: BarChart3 },
  { to: '/settings', label: 'Settings', icon: Cog },
];

function Brand() {
  return (
    <NavLink to="/" className="flex items-center gap-2.5 group">
      <span className="relative h-7 w-7 rounded-lg bg-gradient-to-br from-accent to-accent-hover grid place-items-center shadow-accent-glow">
        <span className="h-2.5 w-2.5 rounded-sm bg-white" />
      </span>
      <span className="text-base font-semibold tracking-tight">
        <span className="text-fg">Live</span>
        <span className="text-accent">Coach</span>
      </span>
    </NavLink>
  );
}

function NavList({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <nav className="p-3 flex-1 space-y-0.5">
      {nav.map(({ to, label, icon: Icon, end }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          onClick={onNavigate}
          className={({ isActive }) =>
            `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all ${
              isActive
                ? 'bg-accent-soft text-accent ring-1 ring-inset ring-accent/20'
                : 'text-fg-muted hover:text-fg hover:bg-white/[0.04]'
            }`
          }
        >
          <Icon size={16} />
          {label}
        </NavLink>
      ))}
    </nav>
  );
}

export default function Layout() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const location = useLocation();

  useEffect(() => { setDrawerOpen(false); }, [location.pathname]);

  useEffect(() => {
    if (!drawerOpen) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setDrawerOpen(false); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [drawerOpen]);

  return (
    <div className="min-h-screen flex flex-col bg-bg text-fg">
      <DemoBanner />

      <header className="md:hidden flex items-center justify-between px-4 py-3 border-b border-white/[0.06] bg-bg-card/60 backdrop-blur sticky top-0 z-30">
        <Brand />
        <button onClick={() => setDrawerOpen(true)} className="btn-ghost p-2" aria-label="Open menu">
          <Menu size={18} />
        </button>
      </header>

      <div className="flex-1 flex">
        <aside className="hidden md:flex md:flex-col w-60 border-r border-white/[0.06] bg-bg-card/40 backdrop-blur sticky top-0 h-screen">
          <div className="p-5 border-b border-white/[0.06]"><Brand /></div>
          <NavList />
          <div className="p-3 border-t border-white/[0.06] text-[11px] text-fg-dim">
            TwitchCon × OpenAI Codex
          </div>
        </aside>

        {drawerOpen && (
          <div className="md:hidden fixed inset-0 z-40">
            <div className="absolute inset-0 bg-black/60 backdrop-blur-sm animate-fade-in" onClick={() => setDrawerOpen(false)} />
            <div className="relative h-full w-72 max-w-[85vw] bg-bg-card border-r border-white/10 flex flex-col animate-fade-up">
              <div className="p-5 border-b border-white/[0.06] flex items-center justify-between">
                <Brand />
                <button onClick={() => setDrawerOpen(false)} className="btn-ghost p-2" aria-label="Close menu">
                  <X size={18} />
                </button>
              </div>
              <NavList onNavigate={() => setDrawerOpen(false)} />
            </div>
          </div>
        )}

        <main className="flex-1 min-w-0">
          <div className="p-4 md:p-8 max-w-6xl w-full mx-auto">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
