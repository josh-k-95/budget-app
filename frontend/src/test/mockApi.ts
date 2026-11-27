import { vi } from 'vitest';

type Handler = (init: RequestInit | undefined) => Response | Promise<Response>;

/**
 * Stub global fetch with per-route handlers keyed by "METHOD /api/path".
 * Unknown routes fail loudly so tests notice unexpected requests.
 */
export function mockApi(routes: Record<string, Handler>) {
  const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
    const url = typeof input === 'string' ? input : input.toString();
    const key = `${init?.method ?? 'GET'} ${url}`;
    const handler = routes[key];
    if (!handler) return Promise.reject(new Error(`Unexpected request: ${key}`));
    return Promise.resolve(handler(init));
  });
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

export const json = (body: unknown, status = 200) => Response.json(body, { status });

export const unauthenticated = () => json({ detail: 'Not authenticated' }, 401);

export const testUser = {
  id: '00000000-0000-4000-8000-000000000001',
  username: 'alice',
  budgets: [{ id: '00000000-0000-4000-8000-0000000000b1', name: 'Personal', role: 'owner' }],
};
