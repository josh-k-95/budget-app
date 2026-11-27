import { Link } from 'react-router';

export function NotFoundPage() {
  return (
    <section aria-labelledby="not-found-heading">
      <h1 id="not-found-heading" className="text-2xl font-bold">
        Page not found
      </h1>
      <Link to="/" className="mt-2 inline-block text-teal-700 underline dark:text-teal-400">
        Go home
      </Link>
    </section>
  );
}
