import { Link, Navigate, useNavigate, useSearchParams } from 'react-router';
import { useAuth } from '../auth/AuthProvider';
import { safeNext } from '../auth/next';
import { AuthForm } from '../components/AuthForm';
import { useAppConfig } from '../config';

export function RegisterPage() {
  const { state, register } = useAuth();
  const { signup_open } = useAppConfig();
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const next = safeNext(params.get('next'));

  if (state.status === 'authenticated') return <Navigate to={next} replace />;

  const signInLink = (
    <Link
      to={`/login?next=${encodeURIComponent(next)}`}
      className="text-teal-700 underline dark:text-teal-400"
    >
      Sign in
    </Link>
  );

  if (!signup_open) {
    return (
      <section aria-labelledby="closed-heading" className="mx-auto max-w-sm">
        <h1 id="closed-heading" className="text-2xl font-bold">
          Registration is closed
        </h1>
        <p className="mt-2 text-slate-700 dark:text-slate-300">
          Ask the server admin for an account. Already have one? {signInLink}
        </p>
      </section>
    );
  }

  return (
    <AuthForm
      title="Create account"
      submitLabel="Create account"
      passwordAutoComplete="new-password"
      passwordHint="Use a long password you don’t use anywhere else."
      onSubmit={async (credentials) => {
        await register(credentials);
        void navigate(next, { replace: true });
      }}
      footer={<p>Already have an account? {signInLink}</p>}
    />
  );
}
