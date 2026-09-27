import { CT6_API_BASE_URL } from "./config";

export async function loadPilotLimits(signal: AbortSignal): Promise<string | null> {
  try {
    const response = await fetch(`${CT6_API_BASE_URL}/api/pilot/v1/capabilities`, {
      credentials: "include", signal,
    });
    if (!response.ok) return null;
    const data: unknown = await response.json();
    if (typeof data !== "object" || data === null || !("limits" in data)) return null;
    const limits = data.limits;
    if (typeof limits !== "object" || limits === null) return null;
    const values = limits as Record<string, unknown>;
    if (!["max_trials", "max_occurrences", "max_layers", "max_hours_components"].every(
      (field) => Number.isSafeInteger(values[field]) && Number(values[field]) > 0,
    )) return null;
    return `Up to ${values.max_trials} trials, ${values.max_occurrences} occurrences, ${values.max_layers} layers or ${values.max_hours_components} hours-clause components per request.`;
  } catch { return null; }
}
