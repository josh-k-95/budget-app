import { Outlet } from 'react-router';
import { useAuth } from '../auth/AuthProvider';
import { useAppConfig } from '../config';

export function Layout() {
  const { app_name } = useAppConfig();
  const { state, logout } = useAuth();
  return (
    <div className="min-h-dvh bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <header className="flex items-center justify-between gap-4 border-b border-slate-200 bg-white px-4 py-3 dark:border-slate-800 dark:bg-slate-900">
        <p className="text-lg font-semibold">{app_name}</p>
        {state.status === 'authenticated' && (
          <div className="flex items-center gap-3 text-sm">
            <span className="hidden text-slate-700 sm:inline dark:text-slate-300">
              {state.user.username}
            </span>
            <button
              type="button"
              onClick={() => void logout()}
              className="rounded-md border border-slate-400 px-3 py-1.5 font-medium hover:bg-slate-100 dark:border-slate-600 dark:hover:bg-slate-800"
            >
              Log out
            </button>
          </div>
        )}
      </header>
      <main className="mx-auto max-w-5xl px-4 py-6">
        <Outlet />
      </main>
    </div>
  );
}
