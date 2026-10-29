import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import Layout from '@/components/Layout';
import PageTransition from '@/components/PageTransition';
import Landing from '@/features/landing/Landing';
import Dashboard from '@/features/dashboard/Dashboard';
import Suggestions from '@/features/suggestions/Suggestions';
import Polls from '@/features/polls/Polls';
import Settings from '@/features/settings/Settings';
import NotFound from '@/features/NotFound';

export default function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<PageTransition><Landing /></PageTransition>} />
            <Route path="/dashboard" element={<PageTransition><Dashboard /></PageTransition>} />
            <Route path="/suggestions" element={<PageTransition><Suggestions /></PageTransition>} />
            <Route path="/polls" element={<PageTransition><Polls /></PageTransition>} />
            <Route path="/settings" element={<PageTransition><Settings /></PageTransition>} />
            <Route path="*" element={<PageTransition><NotFound /></PageTransition>} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  );
}
