import { render, screen, within } from "@testing-library/react";

import { CatalogueResults } from "../features/results/CatalogueResults";
import { ct6SuccessFixture } from "./fixtures/ct6Success";

describe("authoritative catalogue result hierarchy", () => {
  it("renders warnings, pre/post-capacity values, three-way settlement and audit identities", () => {
    render(<CatalogueResults data={ct6SuccessFixture()} freshness="current" />);
    expect(screen.getByRole("heading", { name: "Warnings" })).toBeVisible();
    expect(screen.getAllByText("$20,000,000.00", { selector: "strong" }).length).toBeGreaterThan(0);
    expect(screen.getByText("$1,000,000.00", { selector: "strong" })).toBeVisible();
    expect(screen.getByText("$19,000,000.00", { selector: "strong" })).toBeVisible();
    expect(screen.getByRole("heading", { name: "Versions, hashes and reconciliations" })).toBeVisible();
    expect(screen.getByText("a".repeat(64))).toBeVisible();
    expect(screen.getByRole("table", { name: "Authoritative reconciliations" })).toBeVisible();
  });

  it("preserves negative net cash without flooring", () => {
    render(<CatalogueResults data={ct6SuccessFixture({ negativeCash: true })} freshness="current" />);
    expect(screen.getByText("-$1,000,000.00", { selector: "strong" })).toBeVisible();
  });

  it("displays null utilization as N/A with its status", () => {
    render(<CatalogueResults data={ct6SuccessFixture({ zeroCapacity: true })} freshness="current" />);
    expect(screen.getByText("N/A – no payable capacity")).toBeVisible();
    expect(screen.getByText("not applicable zero capacity")).toBeVisible();
  });

  it("identifies deliberately omitted occurrence rows in summary mode", () => {
    render(<CatalogueResults data={ct6SuccessFixture({ summary: true })} freshness="current" />);
    expect(screen.getByText(/occurrence rows were omitted by the requested summary response/i)).toBeVisible();
  });

  it("labels stale authoritative output without changing its values", () => {
    render(<CatalogueResults data={ct6SuccessFixture()} freshness="stale" />);
    expect(screen.getByLabelText("Stale prior authoritative result")).toBeVisible();
  });

  it("G95 preserves and renders every returned empirical OEP point without interpolation", () => {
    render(<CatalogueResults data={ct6SuccessFixture()} freshness="current" />);
    const table = screen.getByRole("table", { name: /authoritative OEP points/i });
    expect(table.querySelectorAll("tbody tr")).toHaveLength(2);
    expect(within(table).getByText("$40,500,000.00", { selector: "td" })).toBeVisible();
    expect(within(table).getByText("$12,000,000.00", { selector: "td" })).toBeVisible();
    expect(screen.getByRole("img", { name: /subject-loss occurrence exceedance curve/i }).querySelectorAll("circle")).toHaveLength(2);
  });
});
