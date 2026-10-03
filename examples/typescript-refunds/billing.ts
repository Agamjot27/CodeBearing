// Round once after summing; individual rounding can change the refund total.
export function roundTotal(amount: number): number {
  return Math.round(amount * 100) / 100;
}

export default function refundTotal(amounts: number[]): number {
  return roundTotal(amounts.reduce((total, amount) => total + amount, 0));
}
