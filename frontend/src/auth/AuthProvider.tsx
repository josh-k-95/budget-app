import {
  createContext,
  use,
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import * as authApi from '../api/auth';
import type { Credentials, User } from '../api/auth';

export type AuthState =
  { status: 'loading' } | { status: 'anonymous' } | { status: 'authenticated'; user: User };

interface AuthContextValue {
  state: AuthState;
  login: (credentials: Credentials) => Promise<void>;
  register: (credentials: Credentials) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({ status: 'loading' });

  useEffect(() => {
    let cancelled = false;
    authApi
      .me()
      .then((user) => {
        if (!cancelled)
          setState(user ? { status: 'authenticated', user } : { status: 'anonymous' });
      })
      .catch(() => {
        if (!cancelled) setState({ status: 'anonymous' });
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(async (credentials: Credentials) => {
    const user = await authApi.login(credentials);
    setState({ status: 'authenticated', user });
  }, []);

  const register = useCallback(async (credentials: Credentials) => {
    const user = await authApi.register(credentials);
    setState({ status: 'authenticated', user });
  }, []);

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } finally {
      setState({ status: 'anonymous' });
    }
  }, []);

  const value = useMemo(
    () => ({ state, login, register, logout }),
    [state, login, register, logout],
  );
  return <AuthContext value={value}>{children}</AuthContext>;
}

export function useAuth(): AuthContextValue {
  const value = use(AuthContext);
  if (!value) throw new Error('useAuth must be used inside <AuthProvider>');
  return value;
}
