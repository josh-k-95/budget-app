/**
 * Sanitise a post-login redirect target. Only same-site relative paths are allowed:
 * must start with "/", must not start with "//" or "/\" (browsers treat "\" like "/", so both
 * are protocol-relative URLs to another host), and must not contain control characters.
 * Anything else falls back to "/".
 */
export function safeNext(value: string | null | undefined): string {
  if (!value || !value.startsWith('/')) return '/';
  if (value.startsWith('//') || value.startsWith('/\\')) return '/';
  // eslint-disable-next-line no-control-regex
  if (/[\u0000-\u001f\u007f]/.test(value)) return '/';
  return value;
}
