import { createContext, use, useEffect, useState, type ReactNode } from 'react';
import { getConfig, type AppConfig } from './api/config';

export const DEFAULT_APP_NAME = 'Budget App';

const DEFAULT_CONFIG: AppConfig = { app_name: DEFAULT_APP_NAME, signup_open: false };

const AppConfigContext = createContext<AppConfig>(DEFAULT_CONFIG);

/** Loads the app name (and future config) once from the backend. */
export function AppConfigProvider({ children }: { children: ReactNode }) {
  const [config, setConfig] = useState<AppConfig>(DEFAULT_CONFIG);

  useEffect(() => {
    let cancelled = false;
    getConfig()
      .then((loaded) => {
        if (!cancelled) setConfig(loaded);
      })
      .catch(() => {
        // Backend unreachable: keep the default name.
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    document.title = config.app_name;
  }, [config.app_name]);

  return <AppConfigContext value={config}>{children}</AppConfigContext>;
}

export function useAppConfig(): AppConfig {
  return use(AppConfigContext);
}
