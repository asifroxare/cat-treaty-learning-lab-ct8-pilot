import { expectTypeOf } from "vitest";

import type { AuthoritativeNumber, AuthoritativeSuccessResponse } from "../api/authoritative";
import type { CatalogueRunRequest, CT6Problem, HoursRunRequest } from "../api/contract";

describe("generated CT6 contract", () => {
  it("freezes request schema literals and problem fields", () => {
    expectTypeOf<CatalogueRunRequest["api_schema_version"]>().toEqualTypeOf<"ct6.0">();
    expectTypeOf<HoursRunRequest["api_schema_version"]>().toEqualTypeOf<"ct6.0">();
    expectTypeOf<CT6Problem["code"]>().toEqualTypeOf<string>();
  });

  it("brands every projected response number at the API boundary", () => {
    expectTypeOf<AuthoritativeSuccessResponse["post_capacity"]["annual_rows"][number]["gross_contractual_recovery"]>()
      .toEqualTypeOf<AuthoritativeNumber>();
    expectTypeOf<AuthoritativeSuccessResponse["post_capacity"]["annual_rows"][number]["net_cash_settlement"]>()
      .toEqualTypeOf<AuthoritativeNumber>();
  });
});
