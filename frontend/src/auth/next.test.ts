import { describe, expect, it } from 'vitest';
import { safeNext } from './next';

describe('safeNext', () => {
  it.each(['/', '/transactions', '/transactions/2026-11?view=cards', '/a//b'])(
    'keeps same-site path %s',
    (path) => {
      expect(safeNext(path)).toBe(path);
    },
  );

  it.each([
    ['protocol-relative', '//evil.com'],
    ['backslash protocol-relative', '/\\evil.com'],
    ['absolute URL', 'https://evil.com'],
    ['javascript URL', 'javascript:alert(1)'],
    ['relative without slash', 'evil'],
    ['empty', ''],
    ['control character', '/\t/evil.com'],
    ['newline', '/ok\nLocation: x'],
  ])('rejects %s', (_label, value) => {
    expect(safeNext(value)).toBe('/');
  });

  it('defaults when missing', () => {
    expect(safeNext(null)).toBe('/');
    expect(safeNext(undefined)).toBe('/');
  });
});
