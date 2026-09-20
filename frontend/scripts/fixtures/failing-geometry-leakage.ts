declare const pixelBrand: unique symbol;
type CssPixel = number & { readonly [pixelBrand]: true };

export function leakGeometry(width: CssPixel): string {
  return JSON.stringify(width);
}
