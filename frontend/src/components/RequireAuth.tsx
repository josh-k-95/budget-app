import { Navigate, Outlet, useLocation } from 'react-router';
import { useAuth } from '../auth/AuthProvider';

/** Route guard: renders child routes only for signed-in users. */
export function RequireAuth() {
  const { state } = useAuth();
  const location = useLocation();

  if (state.status === 'loading') {
    return (
      <p role="status" className="text-slate-700 dark:text-slate-300">
        Loading…
      </p>
    );
  }
  if (state.status === 'anonymous') {
    const next = encodeURIComponent(location.pathname + location.search);
    return <Navigate to={`/login?next=${next}`} replace />;
  }
  return <Outlet />;
}
