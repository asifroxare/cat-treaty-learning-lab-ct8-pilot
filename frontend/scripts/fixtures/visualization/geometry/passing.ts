declare const authoritativeBrand: unique symbol;
declare const pixelBrand: unique symbol;
type AuthoritativeNumber = number & { readonly [authoritativeBrand]: true };
type CssPixel = number & { readonly [pixelBrand]: true };

export function towerWidth(layerLimit: AuthoritativeNumber, maximumLimit: AuthoritativeNumber, trackWidth: number): CssPixel {
  return (layerLimit / maximumLimit * trackWidth) as CssPixel;
}
