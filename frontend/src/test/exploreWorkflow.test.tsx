import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { MemoryRouter } from "react-router-dom";

import type { CT6Client, RunSuccess } from "../api/client";
import { App } from "../app/App";
import { ExploreTreatyPage } from "../features/explore/ExploreTreatyPage";
import { CatalogueRunProvider } from "../features/explore/useCatalogueRun";
import { ct6SuccessFixture } from "./fixtures/ct6Success";

function successfulClient(): { client: CT6Client; runCatalogue: ReturnType<typeof vi.fn> } {
  const success: RunSuccess = {
    ok: true,
    requestId: "request-ct7",
    data: ct6SuccessFixture(),
  };
  const runCatalogue = vi.fn(async () => success);
  return {
    runCatalogue,
    client: { runCatalogue, runHoursClause: vi.fn() },
  };
}

function renderExplore(client: CT6Client) {
  return render(<CatalogueRunProvider client={client}><ExploreTreatyPage /></CatalogueRunProvider>);
}

describe("Explore Treaty workflow", () => {
  it("builds and submits a complete catalogue request", async () => {
    const user = userEvent.setup();
    const { client, runCatalogue } = successfulClient();
    renderExplore(client);

    await user.click(screen.getByRole("button", { name: "Run treaty scenario" }));
    await waitFor(() => expect(runCatalogue).toHaveBeenCalledTimes(1));
    expect(runCatalogue.mock.calls[0][0]).toMatchObject({
      api_schema_version: "ct6.0",
      input: { simulation: { simulation_id: "S1" } },
    });
    expect(screen.getByRole("heading", { name: "Authoritative run completed" })).toBeVisible();
    expect(screen.getAllByText(/request-ct7/).length).toBeGreaterThan(0);
  });

  it("marks an existing successful result stale after a contractual edit", async () => {
    const user = userEvent.setup();
    const { client } = successfulClient();
    renderExplore(client);
    await user.click(screen.getByRole("button", { name: "Run treaty scenario" }));
    await screen.findByRole("heading", { name: "Authoritative run completed" });

    const attachment = screen.getByRole("textbox", { name: "Occurrence attachment" });
    await user.clear(attachment);
    await user.type(attachment, "12000000");
    expect(screen.getByRole("heading", { name: "Previous result — inputs changed" })).toBeVisible();
    expect(screen.getByText("editing", { selector: "strong" })).toBeVisible();
  });

  it("retains only a labelled stale prior result when the edited run fails", async () => {
    const user = userEvent.setup();
    const success: RunSuccess = { ok: true, requestId: "request-old", data: ct6SuccessFixture() };
    const runCatalogue = vi.fn()
      .mockResolvedValueOnce(success)
      .mockResolvedValueOnce({
        ok: false,
        state: "domain_error",
        requestId: "request-failed",
        problem: {
          type: "about:blank", title: "Treaty terms invalid", status: 422,
          detail: "The treaty contract is invalid.", instance: "/api/v1/runs/catalogue",
          request_id: "request-failed", code: "CT6_DOMAIN_VALIDATION", errors: [],
        },
      });
    const client: CT6Client = { runCatalogue, runHoursClause: vi.fn() };
    renderExplore(client);
    await user.click(screen.getByRole("button", { name: "Run treaty scenario" }));
    await screen.findByRole("heading", { name: "Authoritative run completed" });
    await user.type(screen.getByRole("textbox", { name: "Peril" }), "storm");
    await user.click(screen.getByRole("button", { name: "Run treaty scenario" }));

    expect(await screen.findByRole("heading", { name: "Treaty terms invalid" })).toBeVisible();
    expect(screen.getByRole("heading", { name: "Previous result — inputs changed" })).toBeVisible();
    expect(screen.getByText("domain error", { selector: "strong" })).toBeVisible();
    expect(screen.getByText(/request-old/)).toBeVisible();
  });

  it("blocks an incomplete request and maps the error to its field", async () => {
    const user = userEvent.setup();
    const { client, runCatalogue } = successfulClient();
    renderExplore(client);
    const eventId = screen.getByRole("textbox", { name: "Event ID" });
    await user.clear(eventId);
    await user.click(screen.getByRole("button", { name: "Run treaty scenario" }));

    expect(runCatalogue).not.toHaveBeenCalled();
    expect(eventId).toHaveAttribute("aria-invalid", "true");
    expect(screen.getByRole("heading", { name: "Correct the highlighted request fields" })).toBeVisible();
  });

  it("preserves the latest deterministic identity on the Audit Trail route", async () => {
    const user = userEvent.setup();
    const { client } = successfulClient();
    render(<MemoryRouter initialEntries={["/explore"]}><App client={client} /></MemoryRouter>);
    await user.click(screen.getByRole("button", { name: "Run treaty scenario" }));
    await screen.findByRole("heading", { name: "Authoritative run completed" });
    await user.click(screen.getByRole("link", { name: "Audit Trail" }));
    expect(screen.getByRole("heading", { name: "Deterministic run identity" })).toBeVisible();
    expect(screen.getByText("a".repeat(64))).toBeVisible();
    expect(screen.getByText("request-ct7")).toBeVisible();
  });
});
