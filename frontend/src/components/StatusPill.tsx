type Kind =
  | 'proposed' | 'approved' | 'executed' | 'rejected' | 'failed'
  | 'active' | 'completed' | 'terminated' | 'archived' | 'moderated' | 'invalid'
  | 'live' | 'offline';

const map: Record<Kind, { label: string; cls: string; dot: string; pulse: boolean }> = {
  proposed:   { label: 'Proposed',   cls: 'bg-accent-soft text-accent ring-accent/30',    dot: 'bg-accent', pulse: true },
  approved:   { label: 'Approved',   cls: 'bg-ok/10 text-ok ring-ok/30',                  dot: 'bg-ok',     pulse: false },
  executed:   { label: 'Executed',   cls: 'bg-ok/10 text-ok ring-ok/30',                  dot: 'bg-ok',     pulse: false },
  rejected:   { label: 'Rejected',   cls: 'bg-white/[0.06] text-fg-muted ring-white/10',  dot: 'bg-fg-dim', pulse: false },
  failed:     { label: 'Failed',     cls: 'bg-bad/10 text-bad ring-bad/30',               dot: 'bg-bad',    pulse: false },
  active:     { label: 'Active',     cls: 'bg-accent-soft text-accent ring-accent/30',    dot: 'bg-accent', pulse: true },
  completed:  { label: 'Completed',  cls: 'bg-ok/10 text-ok ring-ok/30',                  dot: 'bg-ok',     pulse: false },
  terminated: { label: 'Terminated', cls: 'bg-bad/10 text-bad ring-bad/30',               dot: 'bg-bad',    pulse: false },
  archived:   { label: 'Archived',   cls: 'bg-white/[0.06] text-fg-muted ring-white/10',  dot: 'bg-fg-dim', pulse: false },
  moderated:  { label: 'Moderated',  cls: 'bg-warn/10 text-warn ring-warn/30',            dot: 'bg-warn',   pulse: false },
  invalid:    { label: 'Invalid',    cls: 'bg-bad/10 text-bad ring-bad/30',               dot: 'bg-bad',    pulse: false },
  live:       { label: 'Live',       cls: 'bg-bad/10 text-bad ring-bad/30',               dot: 'bg-bad',    pulse: true },
  offline:    { label: 'Offline',    cls: 'bg-white/[0.06] text-fg-muted ring-white/10',  dot: 'bg-fg-dim', pulse: false },
};

export default function StatusPill({ status }: { status: Kind }) {
  const m = map[status];
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${m.cls}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${m.dot} ${m.pulse ? 'animate-pulse-soft' : ''}`} />
      {m.label}
    </span>
  );
}
