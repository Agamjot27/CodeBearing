// .js ESM specifiers are commonly used in TypeScript intended for compilation.
import refundTotal from './billing.js';

export function cancelOrder(lineAmounts: number[]): number {
  return refundTotal(lineAmounts);
}
