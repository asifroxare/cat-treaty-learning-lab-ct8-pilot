import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import type { CT6Client, RunFailure } from "../api/client";
import { ExploreTreatyPage } from "../features/explore/ExploreTreatyPage";
import { CatalogueRunProvider } from "../features/explore/useCatalogueRun";

function renderFailure(failure: RunFailure) {
  const client: CT6Client = { runCatalogue: vi.fn(async () => failure), runHoursClause: vi.fn() };
  return render(<CatalogueRunProvider client={client}><ExploreTreatyPage /></CatalogueRunProvider>);
}

describe("safe error-state presentation", () => {
  it("gives explicit summary guidance for 413 without automatic retry", async () => {
    const user = userEvent.setup();
    const runCatalogue = vi.fn(async () => ({ ok: false as const, state: "too_large" as const, requestId: "large", problem: { type: "about:blank", title: "ignored", status: 413, detail: "ignored", instance: "/api/v1/runs/catalogue", request_id: "large", code: "CT6_REQUEST_TOO_LARGE", errors: [] } }));
    const client: CT6Client = { runCatalogue, runHoursClause: vi.fn() };
    render(<CatalogueRunProvider client={client}><ExploreTreatyPage /></CatalogueRunProvider>);
    await user.click(screen.getByRole("button", { name: "Run treaty scenario" }));
    expect(await screen.findByRole("heading", { name: "The full response would be too large" })).toHaveFocus();
    expect(screen.getByText(/select summary response detail/i)).toBeVisible();
    expect(runCatalogue).toHaveBeenCalledTimes(1);
  });

  it("uses a static sanitized server message instead of supplied internal detail", async () => {
    const user = userEvent.setup();
    renderFailure({ ok: false, state: "server_error", requestId: "failure", problem: { type: "about:blank", title: "C:/secret/path", status: 500, detail: "credential=do-not-leak", instance: "/api/v1/runs/catalogue", request_id: "failure", code: "CT6_INTERNAL_ERROR", errors: [] } });
    await user.click(screen.getByRole("button", { name: "Run treaty scenario" }));
    await waitFor(() => expect(screen.getByRole("heading", { name: "The CT6 service could not complete the run" })).toHaveFocus());
    expect(screen.queryByText(/secret|credential/i)).not.toBeInTheDocument();
  });

  it("distinguishes offline transport without fabricating a problem", async () => {
    const user = userEvent.setup();
    renderFailure({ ok: false, state: "offline", requestId: null, problem: null });
    await user.click(screen.getByRole("button", { name: "Run treaty scenario" }));
    expect(await screen.findByRole("heading", { name: "The CT6 service is unavailable" })).toBeVisible();
    expect(screen.getByText(/no simulated fallback result/i)).toBeVisible();
  });
});
