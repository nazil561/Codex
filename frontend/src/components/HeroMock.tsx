import Sparkline from './Sparkline';

const viewerTrend = [190, 205, 198, 210, 215, 205, 220, 230, 225, 240, 245];
const chatTrend = [80, 82, 78, 85, 90, 88, 87, 92, 86, 84, 87];
const chatterTrend = [30, 32, 28, 33, 35, 34, 32, 36, 34, 33, 34];

export default function HeroMock() {
  return (
    <div className="relative rounded-2xl border border-white/[0.08] bg-bg-card/80 shadow-2xl shadow-black/60 backdrop-blur overflow-hidden">
      <div className="flex items-center gap-1.5 px-4 py-3 border-b border-white/[0.06] bg-bg-elevated/50">
        <span className="h-2.5 w-2.5 rounded-full bg-white/10" />
        <span className="h-2.5 w-2.5 rounded-full bg-white/10" />
        <span className="h-2.5 w-2.5 rounded-full bg-white/10" />
        <span className="ml-3 text-xs text-fg-dim">livecoach · dashboard</span>
      </div>

      <div className="p-5 grid gap-4">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 sm:gap-3">
          {[
            { label: 'Viewers', value: '245', delta: '+4.1%', trend: viewerTrend },
            { label: 'Chat / 15m', value: '87', delta: '+8.6%', trend: chatTrend },
            { label: 'Chatters', value: '34', delta: '+13.3%', trend: chatterTrend },
          ].map((s) => (
            <div key={s.label} className="rounded-xl border border-white/[0.06] bg-bg-elevated/60 p-3">
              <div className="text-[10px] uppercase tracking-wider text-fg-dim">{s.label}</div>
              <div className="mt-1 flex items-baseline gap-1.5">
                <span className="text-lg font-semibold tabular-nums">{s.value}</span>
                <span className="text-[10px] text-ok">{s.delta}</span>
              </div>
              <div className="mt-1 -mx-1"><Sparkline data={s.trend} height={24} /></div>
            </div>
          ))}
        </div>

        <div className="rounded-xl border border-white/[0.06] bg-bg-elevated/40 p-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium">Warmup game?</span>
            <span className="text-[10px] text-accent flex items-center gap-1">
              <span className="h-1.5 w-1.5 rounded-full bg-accent animate-pulse-soft" /> live poll
            </span>
          </div>
          {[
            { label: 'LoL', pct: 22, color: '#9146ff' },
            { label: 'Valorant', pct: 57, color: '#3fb950' },
            { label: 'TFT', pct: 21, color: '#e3b341' },
          ].map((c) => (
            <div key={c.label} className="mb-1.5 last:mb-0">
              <div className="flex justify-between text-[10px] mb-0.5">
                <span className="text-fg-muted">{c.label}</span>
                <span className="text-fg-dim">{c.pct}%</span>
              </div>
              <div className="h-1.5 rounded-full bg-white/[0.04] overflow-hidden">
                <div className="h-full rounded-full" style={{ width: `${c.pct}%`, background: c.color }} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
