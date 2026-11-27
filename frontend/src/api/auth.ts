import { ApiError, apiFetch, apiPost } from './client';

export interface BudgetMembership {
  id: string;
  name: string;
  role: 'owner' | 'member';
}

export interface User {
  id: string;
  username: string;
  budgets: BudgetMembership[];
}

export interface Credentials {
  username: string;
  password: string;
}

export function register(credentials: Credentials): Promise<User> {
  return apiPost<User>('/auth/register', credentials);
}

export function login(credentials: Credentials): Promise<User> {
  return apiPost<User>('/auth/login', credentials);
}

export async function logout(): Promise<void> {
  await apiPost<unknown>('/auth/logout');
}

/** The signed-in user, or null when there is no valid session. */
export async function me(): Promise<User | null> {
  try {
    return await apiFetch<User>('/auth/me');
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) return null;
    throw error;
  }
}
