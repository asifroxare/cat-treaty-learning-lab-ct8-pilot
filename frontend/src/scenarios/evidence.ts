import type { AuthoritativeSuccessResponse } from "../api/authoritative";

export interface EvidenceBackedContent {
  readonly statement: string;
  readonly evidencePaths: readonly string[];
}

const prohibitedNeutralityForms = /\b(recommended|should choose|best option|optimal structure|prefer this election)\b/i;

export function validateNeutralContent(content: EvidenceBackedContent): void {
  if (prohibitedNeutralityForms.test(content.statement)) throw new Error("Guided content contains prohibited recommendation or ranking language");
  if (content.evidencePaths.length === 0) throw new Error("Result-specific content requires evidence paths");
}

export function resolveEvidence(data: AuthoritativeSuccessResponse, content: EvidenceBackedContent): boolean {
  validateNeutralContent(content);
  return content.evidencePaths.every((path) => {
    let current: unknown = data;
    for (const segment of path.split(".")) {
      if (typeof current !== "object" || current === null || !(segment in current)) return false;
      current = (current as Record<string, unknown>)[segment];
    }
    return current !== undefined;
  });
}
