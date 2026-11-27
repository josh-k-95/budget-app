import { describe, expect, it } from 'vitest';
import { sumCents } from './money';

describe('sumCents', () => {
  it('returns 0 for an empty list', () => {
    expect(sumCents([])).toBe(0);
  });

  it('adds integer cents', () => {
    expect(sumCents([1050, 250, 1])).toBe(1301);
  });

  it('rejects non-integer amounts', () => {
    expect(() => sumCents([10.5])).toThrow(TypeError);
    expect(() => sumCents([Number.NaN])).toThrow(TypeError);
  });

  it('rejects totals beyond the safe integer range', () => {
    expect(() => sumCents([Number.MAX_SAFE_INTEGER, 1])).toThrow(RangeError);
  });
});
