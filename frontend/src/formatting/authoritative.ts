import type { AuthoritativeNumber } from "../api/authoritative";

const currencyFormatters = new Map<string, Intl.NumberFormat>();

export function formatCurrency(value: AuthoritativeNumber, currency: string): string {
  let formatter = currencyFormatters.get(currency);
  if (!formatter) {
    formatter = new Intl.NumberFormat("en-US", {
      style: "currency",
      currency,
      maximumFractionDigits: 2,
    });
    currencyFormatters.set(currency, formatter);
  }
  return formatter.format(value);
}

export function formatNumber(value: AuthoritativeNumber): string {
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 4 }).format(value);
}

export function formatInteger(value: AuthoritativeNumber): string {
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(value);
}

export function formatPercent(value: AuthoritativeNumber): string {
  return new Intl.NumberFormat("en-US", { style: "percent", maximumFractionDigits: 2 }).format(value);
}
