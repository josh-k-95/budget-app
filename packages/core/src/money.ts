/**
 * Sum a list of integer minor-unit amounts (cents).
 * Throws if any value is not a safe integer, so float money never slips through.
 */
export function sumCents(amounts: readonly number[]): number {
  let total = 0;
  for (const amount of amounts) {
    if (!Number.isSafeInteger(amount)) {
      throw new TypeError(`Amount must be an integer number of cents, got ${amount}`);
    }
    total += amount;
  }
  if (!Number.isSafeInteger(total)) {
    throw new RangeError('Total exceeds the safe integer range');
  }
  return total;
}
