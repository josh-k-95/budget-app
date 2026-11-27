import { apiFetch } from './client';

export interface AppConfig {
  app_name: string;
}

export function getConfig(): Promise<AppConfig> {
  return apiFetch<AppConfig>('/config');
}
