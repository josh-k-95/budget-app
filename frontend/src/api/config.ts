import { apiFetch } from './client';

export interface AppConfig {
  app_name: string;
  /** Whether the "create account" flow is available. */
  signup_open: boolean;
}

export function getConfig(): Promise<AppConfig> {
  return apiFetch<AppConfig>('/config');
}
