import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import type { CT6Client } from "../api/client";
import { areComparable, ComparePage } from "../features/compare/ComparePage";
import { ct6SuccessFixture } from "./fixtures/ct6Success";

describe("independent side-by-side comparison", () => {
  it("runs two complete requests and shows separate identities without result deltas", async () => {
    const user = userEvent.setup();
    const runCatalogue = vi.fn()
      .mockResolvedValueOnce({ ok: true, requestId: "baseline-request", data: ct6SuccessFixture() })
      .mockResolvedValueOnce({ ok: true, requestId: "scenario-request", data: ct6SuccessFixture() });
    const client: CT6Client = { runCatalogue, runHoursClause: vi.fn() };
    render(<ComparePage client={client} />);
    await user.click(screen.getByRole("button", { name: "Run baseline" }));
    await user.click(screen.getByRole("button", { name: "Run scenario" }));
    await waitFor(() => expect(runCatalogue).toHaveBeenCalledTimes(2));
    expect(runCatalogue.mock.calls[0][0].input.program.layers[0].attachment).toBe(10_000_000);
    expect(runCatalogue.mock.calls[1][0].input.program.layers[0].attachment).toBe(15_000_000);
    expect(screen.getByText("baseline-request")).toBeVisible();
    expect(screen.getByText("scenario-request")).toBeVisible();
    expect(screen.queryByText(/result delta|higher|lower|improvement|recommended/i)).not.toBeInTheDocument();
  });

  it("rejects comparison across different currencies", () => {
    const left = ct6SuccessFixture();
    const right = { ...ct6SuccessFixture(), request: { ...ct6SuccessFixture().request, reporting_currency: "EUR" } };
    expect(areComparable(left, right)).toBe(false);
  });
});
