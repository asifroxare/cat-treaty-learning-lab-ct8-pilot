import type { components } from "./generated/ct6";

declare const authoritativeNumberBrand: unique symbol;

export type AuthoritativeNumber = number & {
  readonly [authoritativeNumberBrand]: "CT6AuthoritativeNumber";
};

type AuthoritativeValue<T> =
  T extends number ? AuthoritativeNumber
    : T extends readonly (infer Item)[] ? readonly AuthoritativeValue<Item>[]
      : T extends object ? { readonly [Key in keyof T]: AuthoritativeValue<T[Key]> }
        : T;

type RawSuccessResponse = components["schemas"]["CT6SuccessResponse"];

export type AuthoritativeSuccessResponse = AuthoritativeValue<RawSuccessResponse>;

export function acceptAuthoritativeResponse(
  response: RawSuccessResponse,
): AuthoritativeSuccessResponse {
  return response as unknown as AuthoritativeSuccessResponse;
}
