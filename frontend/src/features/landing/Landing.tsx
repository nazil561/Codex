import { Link } from 'react-router-dom';
import { ArrowRight, Sparkles, BarChart3, Radio, ShieldCheck, Zap, Eye } from 'lucide-react';
import { isDemoMode, api } from '@/api';
import HeroMock from '@/components/HeroMock';

export default function Landing() {
  return (
    <div className="py-6 md:py-12">
      <section className="relative grid-bg rounded-3xl border border-white/[0.06] overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-bg pointer-events-none" />
        <div className="relative px-6 md:px-12 pt-12 md:pt-16 pb-8">
          <div className="max-w-3xl mx-auto text-center animate-fade-up">
            <div className="inline-flex items-center gap-2 rounded-full border border-accent/30 bg-accent-soft px-3 py-1 text-xs text-accent">
              <Sparkles size={12} /> TwitchCon × OpenAI Codex
            </div>
            <h1 className="mt-6 font-display text-5xl md:text-7xl leading-[1.02] tracking-tight">
              Your chat is talking.<br />
              <span className="italic text-accent">LiveCoach listens.</span>
            </h1>
            <p className="mt-6 text-fg-muted text-base md:text-lg max-w-xl mx-auto">
              Real-time engagement for streamers. Live metrics from Twitch EventSub,
              AI-grounded poll suggestions, and one-click Twitch polls — grounded in
              what your chat is actually doing right now.
            </p>
            <div className="mt-8 flex flex-col sm:flex-row gap-3 justify-center">
              <button
                onClick={() => api.startOAuth()}
                className="btn-primary text-base px-6 py-3"
              >
                {isDemoMode ? 'Try the demo' : 'Connect Twitch'} <ArrowRight size={16} />
              </button>
              <Link to="/dashboard" className="btn-secondary text-base px-6 py-3">
                See the dashboard
              </Link>
            </div>
          </div>

          <div className="max-w-4xl mx-auto mt-12 md:mt-16 animate-fade-up" style={{ animationDelay: '150ms' }}>
            <HeroMock />
          </div>
        </div>
      </section>

      <section className="mt-12 grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { icon: Radio, label: 'EventSub events', value: '5 types' },
          { icon: Zap, label: 'Poll → Twitch', value: '<1s' },
          { icon: Eye, label: 'Individual viewer tracking', value: 'None' },
          { icon: ShieldCheck, label: 'Causality claims', value: 'Zero' },
        ].map(({ icon: Icon, label, value }, i) => (
          <div key={label} className="card p-4 animate-fade-up" style={{ animationDelay: `${200 + i * 60}ms` }}>
            <Icon size={16} className="text-accent" />
            <div className="mt-2 font-display text-2xl">{value}</div>
            <div className="text-xs text-fg-muted mt-0.5">{label}</div>
          </div>
        ))}
      </section>

      <section className="mt-16">
        <div className="max-w-xl">
          <div className="eyebrow">How it works</div>
          <h2 className="mt-2 font-display text-3xl md:text-4xl tracking-tight">Listen. Suggest. Engage.</h2>
        </div>
        <div className="mt-6 grid md:grid-cols-3 gap-4">
          {[
            { icon: Radio, n: '01', title: 'Listen', body: 'Connect Twitch and start an engagement session. We subscribe to chat, poll, and stream events through EventSub.' },
            { icon: Sparkles, n: '02', title: 'Suggest', body: 'When engagement lags, we propose a Twitch poll grounded in your live metrics — with the evidence attached.' },
            { icon: BarChart3, n: '03', title: 'Engage', body: 'Approve a suggestion. A real poll appears on your stream. Watch votes stream back in real time.' },
          ].map(({ icon: Icon, n, title, body }, i) => (
            <div key={n} className="card card-hover p-6 animate-fade-up" style={{ animationDelay: `${i * 80}ms` }}>
              <div className="flex items-center justify-between">
                <Icon size={20} className="text-accent" />
                <span className="font-display text-2xl text-white/10">{n}</span>
              </div>
              <h3 className="mt-4 font-medium">{title}</h3>
              <p className="mt-1.5 text-sm text-fg-muted leading-relaxed">{body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mt-16 card p-6 md:p-8 border-warn/25 bg-warn/[0.04]">
        <div className="flex items-start gap-4">
          <div className="h-10 w-10 rounded-lg bg-warn/10 grid place-items-center shrink-0">
            <ShieldCheck size={20} className="text-warn" />
          </div>
          <div>
            <h3 className="font-medium text-warn">What LiveCoach does and does not claim</h3>
            <p className="mt-1.5 text-sm text-fg-muted leading-relaxed max-w-2xl">
              Suggestions are grounded in metrics we can actually observe — chat volume, unique
              chatters, viewer count, poll activity. We never claim a poll <em>caused</em> an
              outcome. We surface evidence and let you decide. We never identify individual returning
              viewers; Twitch does not provide that data to third-party apps.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
