import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import type { CT6Client } from "../api/client";
import { GuidedLabPage } from "../features/guided/GuidedLabPage";
import { ct6SuccessFixture, hoursSuccessFixture } from "./fixtures/ct6Success";

describe("Guided Lab workflow", () => {
  it("gates independent runs behind a prediction and then resolves evidence", async () => {
    const user = userEvent.setup();
    const runCatalogue = vi.fn(async () => ({ ok: true as const, requestId: `guided-${runCatalogue.mock.calls.length}`, data: ct6SuccessFixture() }));
    const client: CT6Client = { runCatalogue, runHoursClause: vi.fn() };
    render(<GuidedLabPage client={client} />);
    expect(screen.getAllByRole("button", { name: /^E0/ })).toHaveLength(7);
    expect(screen.getByRole("button", { name: "Run baseline" })).toBeDisabled();
    await user.type(screen.getByRole("textbox", { name: /prediction prompt/i }), "I expect the returned subject-loss evidence to respond.");
    await user.click(screen.getByRole("button", { name: "Run baseline" }));
    await user.click(screen.getByRole("button", { name: "Run controlled scenario" }));
    await waitFor(() => expect(runCatalogue).toHaveBeenCalledTimes(2));
    expect(screen.getByRole("heading", { name: "What to carry forward" })).toBeVisible();
    expect(screen.getAllByText(/CT5 result hash/i)).toHaveLength(2);
  });

  it("runs E07 through the hours route and retains candidate evidence paths", async () => {
    const user = userEvent.setup();
    const runHoursClause = vi.fn(async () => ({ ok: true as const, requestId: "guided-hours", data: hoursSuccessFixture() }));
    const client: CT6Client = { runCatalogue: vi.fn(), runHoursClause };
    render(<GuidedLabPage client={client} />);
    await user.click(screen.getByRole("button", { name: /E07/ }));
    await user.type(screen.getByRole("textbox", { name: /prediction prompt/i }), "Validity must be checked before election.");
    await user.click(screen.getByRole("button", { name: "Run baseline" }));
    await user.click(screen.getByRole("button", { name: "Run controlled scenario" }));
    await waitFor(() => expect(runHoursClause).toHaveBeenCalledTimes(2));
    expect(screen.getByText(/contractual admissibility gates election/i)).toBeVisible();
  });
});
