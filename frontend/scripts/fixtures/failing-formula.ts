declare const authoritativeBrand: unique symbol;
type AuthoritativeNumber = number & { readonly [authoritativeBrand]: true };

export function duplicatedRecovery(grossLoss: AuthoritativeNumber, retention: AuthoritativeNumber) {
  return grossLoss - retention;
}
