import { useState, type FormEvent, type ReactNode } from 'react';
import { ApiError } from '../api/client';
import type { Credentials } from '../api/auth';
import { TextField } from './TextField';

interface AuthFormProps {
  title: string;
  submitLabel: string;
  passwordAutoComplete: 'current-password' | 'new-password';
  passwordHint?: string;
  onSubmit: (credentials: Credentials) => Promise<void>;
  footer?: ReactNode;
}

/** Shared username + password form for the login and register pages. */
export function AuthForm({
  title,
  submitLabel,
  passwordAutoComplete,
  passwordHint,
  onSubmit,
  footer,
}: AuthFormProps) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      await onSubmit({ username, password });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong. Please try again.');
      setSubmitting(false);
    }
  }

  return (
    <section
      aria-labelledby="auth-heading"
      className="mx-auto w-full max-w-sm rounded-lg border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900"
    >
      <h1 id="auth-heading" className="text-2xl font-bold">
        {title}
      </h1>
      <form className="mt-6 flex flex-col gap-4" onSubmit={handleSubmit} noValidate>
        <TextField
          label="Username"
          name="username"
          autoComplete="username"
          autoCapitalize="none"
          spellCheck={false}
          required
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
        <TextField
          label="Password"
          name="password"
          type="password"
          autoComplete={passwordAutoComplete}
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          {...(passwordHint ? { hint: passwordHint } : {})}
        />
        <p aria-live="polite" className="min-h-5 text-sm text-red-700 dark:text-red-400">
          {error}
        </p>
        <button
          type="submit"
          disabled={submitting}
          className="rounded-md bg-teal-700 px-4 py-2 font-semibold text-white hover:bg-teal-800 disabled:opacity-60"
        >
          {submitting ? 'Please wait…' : submitLabel}
        </button>
      </form>
      {footer && <div className="mt-4 text-sm">{footer}</div>}
    </section>
  );
}
