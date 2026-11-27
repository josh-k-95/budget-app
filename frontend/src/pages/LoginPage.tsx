import { Link, Navigate, useNavigate, useSearchParams } from 'react-router';
import { useAuth } from '../auth/AuthProvider';
import { safeNext } from '../auth/next';
import { AuthForm } from '../components/AuthForm';
import { useAppConfig } from '../config';

export function LoginPage() {
  const { state, login } = useAuth();
  const { signup_open } = useAppConfig();
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const next = safeNext(params.get('next'));

  if (state.status === 'authenticated') return <Navigate to={next} replace />;

  return (
    <AuthForm
      title="Sign in"
      submitLabel="Sign in"
      passwordAutoComplete="current-password"
      onSubmit={async (credentials) => {
        await login(credentials);
        void navigate(next, { replace: true });
      }}
      footer={
        signup_open && (
          <p>
            New here?{' '}
            <Link
              to={`/register?next=${encodeURIComponent(next)}`}
              className="text-teal-700 underline dark:text-teal-400"
            >
              Create an account
            </Link>
          </p>
        )
      }
    />
  );
}
