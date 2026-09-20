import { render, screen } from "@testing-library/react";
import { createCT6Client } from "../api/client";
import { buildCatalogueRequest, initialCatalogueForm } from "../features/explore/catalogueForm";
import { CatalogueResults } from "../features/results/CatalogueResults";
import { buildHoursRequest, initialHoursForm } from "../features/hours/hoursForm";
import { HoursClauseResults } from "../features/hours/HoursClauseResults";

const baseUrl = import.meta.env.VITE_CT7_REAL_API_URL as string | undefined;
const real = baseUrl ? describe : describe.skip;

real("G103 production client against a real local CT6 API", () => {
  it("completes and renders catalogue and hours-clause runs", async () => {
    const catalogueRequest = buildCatalogueRequest(initialCatalogueForm).request;
    const hoursRequest = buildHoursRequest(initialHoursForm).request;
    expect(catalogueRequest).not.toBeNull(); expect(hoursRequest).not.toBeNull();
    const client = createCT6Client(baseUrl);
    const catalogue = await client.runCatalogue(catalogueRequest!, "ct7-real-catalogue");
    expect(catalogue.ok).toBe(true);
    if (!catalogue.ok) return;
    const first = render(<CatalogueResults data={catalogue.data} freshness="current" />);
    expect(screen.getByRole("heading", { name: /versions, hashes and reconciliations/i })).toBeVisible();
    first.unmount();
    const hours = await client.runHoursClause(hoursRequest!, "ct7-real-hours");
    expect(hours.ok).toBe(true);
    if (!hours.ok) return;
    render(<HoursClauseResults data={hours.data} freshness="current" />);
    expect(screen.getByRole("heading", { name: /candidate admissibility precedes election/i })).toBeVisible();
  }, 30_000);
});
