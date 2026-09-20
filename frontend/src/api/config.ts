function normalizeBaseUrl(value: string): string {
  return value.endsWith("/") ? value.slice(0, -1) : value;
}

export const CT6_API_BASE_URL = normalizeBaseUrl(
  import.meta.env.VITE_CT6_API_BASE_URL ?? "http://localhost:8000",
);
