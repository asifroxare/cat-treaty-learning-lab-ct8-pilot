function normalizeBaseUrl(value: string): string {
  return value.endsWith("/") ? value.slice(0, -1) : value;
}

// A separately built invited-test UI. Default CT7/CT6 builds stay unchanged.
export const CT8_PILOT_MODE = import.meta.env.VITE_CT8_PILOT_MODE === "true";
export const CT8_NOCARD_MODE = CT8_PILOT_MODE && import.meta.env.VITE_CT8_NOCARD_MODE === "true";
export const CT6_API_BASE_URL = CT8_NOCARD_MODE ? "" : normalizeBaseUrl(
  import.meta.env.VITE_CT6_API_BASE_URL ?? "http://localhost:8000",
);
