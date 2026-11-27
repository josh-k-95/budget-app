import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { AppRoutes } from './App';
import { AuthProvider } from './auth/AuthProvider';
import { AppConfigProvider } from './config';
import { json, mockApi, testUser, unauthenticated } from './test/mockApi';

function renderAt(path: string) {
  return render(
    <AppConfigProvider>
      <AuthProvider>
        <MemoryRouter initialEntries={[path]}>
          <AppRoutes />
        </MemoryRouter>
      </AuthProvider>
    </AppConfigProvider>,
  );
}

const config =
  (overrides: Record<string, unknown> = {}) =>
  () =>
    json({ app_name: 'Test Name', signup_open: true, ...overrides });

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('app shell', () => {
  it('shows the app name from /api/config', async () => {
    mockApi({ 'GET /api/config': config(), 'GET /api/auth/me': () => json(testUser) });
    renderAt('/');
    expect(await screen.findByText('Test Name')).toBeInTheDocument();
    expect(document.title).toBe('Test Name');
    expect(await screen.findByRole('heading', { name: 'Welcome' })).toBeInTheDocument();
  });

  it('falls back to the default name when the backend is unreachable', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.reject(new Error('offline'))),
    );
    renderAt('/');
    expect(await screen.findByText('Budget App')).toBeInTheDocument();
  });

  it('renders a not-found page for unknown routes when signed in', async () => {
    mockApi({ 'GET /api/config': config(), 'GET /api/auth/me': () => json(testUser) });
    renderAt('/nope');
    expect(await screen.findByRole('heading', { name: 'Page not found' })).toBeInTheDocument();
  });
});

describe('auth', () => {
  it('redirects signed-out users to the login page', async () => {
    mockApi({ 'GET /api/config': config(), 'GET /api/auth/me': unauthenticated });
    renderAt('/transactions');
    expect(await screen.findByRole('heading', { name: 'Sign in' })).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Page not found' })).not.toBeInTheDocument();
  });

  it('has labelled inputs with the right autocomplete hints', async () => {
    mockApi({ 'GET /api/config': config(), 'GET /api/auth/me': unauthenticated });
    renderAt('/login');
    const username = await screen.findByLabelText('Username');
    const password = screen.getByLabelText('Password');
    expect(username).toHaveAttribute('autocomplete', 'username');
    expect(password).toHaveAttribute('type', 'password');
    expect(password).toHaveAttribute('autocomplete', 'current-password');
  });

  it('signs in and returns to the requested page', async () => {
    const fetchMock = mockApi({
      'GET /api/config': config(),
      'GET /api/auth/me': unauthenticated,
      'POST /api/auth/login': () => json(testUser),
    });
    renderAt('/login?next=%2Fnope');
    fireEvent.change(await screen.findByLabelText('Username'), { target: { value: 'alice' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'correct horse' } });
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }));

    expect(await screen.findByRole('heading', { name: 'Page not found' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Log out' })).toBeInTheDocument();
    const loginCall = fetchMock.mock.calls.find(([, init]) => init?.method === 'POST');
    expect(JSON.parse(String(loginCall?.[1]?.body))).toEqual({
      username: 'alice',
      password: 'correct horse',
    });
  });

  it('ignores an off-site next parameter after login', async () => {
    mockApi({
      'GET /api/config': config(),
      'GET /api/auth/me': unauthenticated,
      'POST /api/auth/login': () => json(testUser),
    });
    renderAt('/login?next=%2F%2Fevil.com');
    fireEvent.change(await screen.findByLabelText('Username'), { target: { value: 'alice' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'correct horse' } });
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }));
    expect(await screen.findByRole('heading', { name: 'Welcome' })).toBeInTheDocument();
  });

  it('shows the server error message on failed login', async () => {
    mockApi({
      'GET /api/config': config(),
      'GET /api/auth/me': unauthenticated,
      'POST /api/auth/login': () => json({ detail: 'Invalid username or password' }, 401),
    });
    renderAt('/login');
    fireEvent.change(await screen.findByLabelText('Username'), { target: { value: 'alice' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'wrong' } });
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }));
    expect(await screen.findByText('Invalid username or password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Sign in' })).toBeEnabled();
  });

  it('shows the create-account link only when signup is open', async () => {
    mockApi({ 'GET /api/config': config(), 'GET /api/auth/me': unauthenticated });
    const { unmount } = renderAt('/login');
    expect(await screen.findByRole('link', { name: 'Create an account' })).toBeInTheDocument();
    unmount();

    mockApi({
      'GET /api/config': config({ signup_open: false }),
      'GET /api/auth/me': unauthenticated,
    });
    renderAt('/login');
    await screen.findByText('Test Name');
    expect(screen.queryByRole('link', { name: 'Create an account' })).not.toBeInTheDocument();
  });

  it('shows a closed message on the register page when signup is closed', async () => {
    mockApi({
      'GET /api/config': config({ signup_open: false }),
      'GET /api/auth/me': unauthenticated,
    });
    renderAt('/register');
    expect(
      await screen.findByRole('heading', { name: 'Registration is closed' }),
    ).toBeInTheDocument();
  });

  it('logs out and returns to the login page', async () => {
    mockApi({
      'GET /api/config': config(),
      'GET /api/auth/me': () => json(testUser),
      'POST /api/auth/logout': () => new Response(null, { status: 204 }),
    });
    renderAt('/');
    fireEvent.click(await screen.findByRole('button', { name: 'Log out' }));
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Sign in' })).toBeInTheDocument();
    });
  });
});
