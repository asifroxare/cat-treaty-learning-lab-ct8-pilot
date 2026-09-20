import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import type { CT6Client } from "../api/client";
import { HoursClausePage } from "../features/hours/HoursClausePage";
import { HoursRunProvider } from "../features/hours/useHoursRun";
import { hoursSuccessFixture } from "./fixtures/ct6Success";

function setupClient() {
  const runHoursClause = vi.fn(async () => ({ ok: true as const, requestId: "hours-request", data: hoursSuccessFixture() }));
  const client: CT6Client = { runHoursClause, runCatalogue: vi.fn() };
  return { client, runHoursClause };
}

describe("Hours-Clause Lab workflow", () => {
  it("submits to the dedicated route and renders election plus exclusion evidence", async () => {
    const user = userEvent.setup();
    const { client, runHoursClause } = setupClient();
    render(<HoursRunProvider client={client}><HoursClausePage /></HoursRunProvider>);
    await user.click(screen.getByRole("button", { name: "Generate and elect occurrence" }));
    await waitFor(() => expect(runHoursClause).toHaveBeenCalledTimes(1));
    expect(screen.getByRole("heading", { name: "Candidate admissibility precedes election" })).toBeVisible();
    expect(screen.getByText("SET-003")).toBeVisible();
    expect(screen.getByText(/duplicate_component/)).toBeVisible();
    expect(screen.getByText(/not calculated for excluded set/i)).toBeVisible();
    expect(screen.getByText(/never admits them into contractual election/i)).toBeVisible();
  });

  it("enables manual candidate input only for manual election", async () => {
    const user = userEvent.setup();
    const { client } = setupClient();
    render(<HoursRunProvider client={client}><HoursClausePage /></HoursRunProvider>);
    const manual = screen.getByRole("textbox", { name: "Manual candidate-set ID" });
    expect(manual).toBeDisabled();
    await user.selectOptions(screen.getByRole("combobox", { name: "Selected election method" }), "manual");
    expect(manual).toBeEnabled();
    await user.click(screen.getByRole("button", { name: "Generate and elect occurrence" }));
    expect(manual).toHaveAttribute("aria-invalid", "true");
  });

  it("keeps contract blockage separate from any prior result", async () => {
    const user = userEvent.setup();
    const runHoursClause = vi.fn()
      .mockResolvedValueOnce({ ok: true, requestId: "old-hours", data: hoursSuccessFixture() })
      .mockResolvedValueOnce({ ok: false, state: "contract_blocked", requestId: "blocked", problem: { type: "about:blank", title: "Contract blocked", status: 422, detail: "No valid election could be made.", instance: "/api/v1/runs/hours-clause", request_id: "blocked", code: "CT6_CONTRACT_BLOCKED", errors: [{ path: "input.terms", code: "CT6_CONTRACT_BLOCKED", message: "Election is blocked.", rule_reference: "CT4-hours" }] } });
    const client: CT6Client = { runHoursClause, runCatalogue: vi.fn() };
    render(<HoursRunProvider client={client}><HoursClausePage /></HoursRunProvider>);
    await user.click(screen.getByRole("button", { name: "Generate and elect occurrence" }));
    await screen.findByRole("heading", { name: "Authoritative hours-clause run completed" });
    await user.clear(screen.getByRole("textbox", { name: "Hours duration" }));
    await user.type(screen.getByRole("textbox", { name: "Hours duration" }), "48");
    await user.click(screen.getByRole("button", { name: "Generate and elect occurrence" }));
    expect(await screen.findByRole("heading", { name: "Contract blocked" })).toBeVisible();
    expect(screen.getByRole("heading", { name: "Previous result — inputs changed" })).toBeVisible();
    expect(screen.getByText("contract blocked", { selector: "strong" })).toBeVisible();
  });
});
