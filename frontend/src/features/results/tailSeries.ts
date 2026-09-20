import type { AuthoritativeNumber } from "../../api/authoritative";

export interface EmpiricalTailPoint {
  readonly rank: AuthoritativeNumber;
  readonly loss: AuthoritativeNumber;
  readonly exceedanceProbability: AuthoritativeNumber;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

/** Read-only adapter for the frozen CT4 empirical curve wire shape. */
export function subjectOepPoints(payload: Readonly<Record<string, unknown>>): readonly EmpiricalTailPoint[] {
  const perspectives = payload.perspectives;
  if (!Array.isArray(perspectives)) return [];
  const subject = perspectives.find((item) => isRecord(item) && item.perspective === "subject_loss");
  if (!isRecord(subject) || !Array.isArray(subject.oep_curve)) return [];
  const points: EmpiricalTailPoint[] = [];
  for (const item of subject.oep_curve) {
    if (!isRecord(item) || typeof item.rank !== "number" || typeof item.loss !== "number"
        || typeof item.exceedance_probability !== "number") return [];
    points.push({
      rank: item.rank as AuthoritativeNumber,
      loss: item.loss as AuthoritativeNumber,
      exceedanceProbability: item.exceedance_probability as AuthoritativeNumber,
    });
  }
  return points;
}
