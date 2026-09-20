import type { AuthoritativeNumber } from "../../api/authoritative";

declare const cssPixelBrand: unique symbol;
export type CssPixel = number & { readonly [cssPixelBrand]: "CssPixel" };

const TRACK_WIDTH = 240;

export interface RecoveryBarGeometry {
  readonly subjectLossWidth: CssPixel;
  readonly preCapacityWidth: CssPixel;
  readonly postCapacityWidth: CssPixel;
}

function scale(value: AuthoritativeNumber, maximum: AuthoritativeNumber): CssPixel {
  if (maximum <= 0) return 0 as CssPixel;
  return Math.max(0, Math.min(TRACK_WIDTH, (value / maximum) * TRACK_WIDTH)) as CssPixel;
}

export function recoveryBarGeometry(
  subjectLoss: AuthoritativeNumber,
  preCapacityRecovery: AuthoritativeNumber,
  postCapacityRecovery: AuthoritativeNumber,
): RecoveryBarGeometry {
  return {
    subjectLossWidth: scale(subjectLoss, subjectLoss),
    preCapacityWidth: scale(preCapacityRecovery, subjectLoss),
    postCapacityWidth: scale(postCapacityRecovery, subjectLoss),
  };
}

export function asCssPixels(value: CssPixel): string {
  return `${value}px`;
}
