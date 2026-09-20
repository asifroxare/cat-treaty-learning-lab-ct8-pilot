import axe from "axe-core";
import { render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";

import type { CT6Client } from "../api/client";
import { App } from "../app/App";
import { CatalogueResults } from "../features/results/CatalogueResults";
import { ct6SuccessFixture } from "./fixtures/ct6Success";

const client: CT6Client = {
  runCatalogue: vi.fn(),
  runHoursClause: vi.fn(),
};

describe("automated accessibility baseline", () => {
  it.each(["/", "/guided", "/explore", "/hours-clause", "/compare", "/audit"])("has no detectable axe violations at %s", async (path) => {
    const { container } = render(<MemoryRouter initialEntries={[path]}><App client={client} /></MemoryRouter>);
    const result = await axe.run(container, { rules: { "color-contrast": { enabled: false } } });
    expect(result.violations).toEqual([]);
  });

  it("keeps the complete authoritative result hierarchy machine-readable", async () => {
    const { container } = render(<CatalogueResults data={ct6SuccessFixture()} freshness="current" />);
    const result = await axe.run(container, { rules: { "color-contrast": { enabled: false } } });
    expect(result.violations).toEqual([]);
  });
});
