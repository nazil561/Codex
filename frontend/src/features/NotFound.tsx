import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="py-20 text-center">
      <div className="font-display text-7xl tracking-tight text-accent/40">404</div>
      <h1 className="mt-3 font-display text-3xl tracking-tight">Not found</h1>
      <p className="mt-2 text-sm text-fg-muted">This page doesn't exist.</p>
      <Link to="/dashboard" className="btn-secondary mt-6 inline-flex">
        <ArrowLeft size={14} /> Back to dashboard
      </Link>
    </div>
  );
}
