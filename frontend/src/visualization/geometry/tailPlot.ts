import type { AuthoritativeNumber } from "../../api/authoritative";

declare const coordinateBrand: unique symbol;
export type SvgCoordinate = number & { readonly [coordinateBrand]: "SvgCoordinate" };
export interface TailPlotGeometry { readonly x: SvgCoordinate; readonly y: SvgCoordinate }

export function tailPointGeometry(
  probability: AuthoritativeNumber,
  loss: AuthoritativeNumber,
  maximumLoss: AuthoritativeNumber,
): TailPlotGeometry {
  const x = Math.max(0, Math.min(100, probability * 100)) as SvgCoordinate;
  const y = (maximumLoss <= 0 ? 100 : 100 - Math.max(0, Math.min(100, (loss / maximumLoss) * 100))) as SvgCoordinate;
  return { x, y };
}
