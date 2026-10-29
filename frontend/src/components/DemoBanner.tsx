import { isDemoMode } from '@/api';

export default function DemoBanner() {
  if (!isDemoMode) return null;
  return (
    <div className="bg-warn/10 border-b border-warn/30 text-warn text-xs px-4 py-1.5 text-center">
      Demo mode — showing sample data, not live Twitch data.
    </div>
  );
}
