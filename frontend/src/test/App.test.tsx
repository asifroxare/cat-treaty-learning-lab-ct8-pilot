import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";

import { App } from "../app/App";

function renderAt(path = "/") {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  );
}

describe("CT7 foundation routes", () => {
  it("renders a clearly separated treaty-learning identity and disclaimer", () => {
    renderAt();
    expect(screen.getByRole("heading", { level: 1, name: /see what happened/i })).toBeVisible();
    expect(screen.getByText(/not the cat xol pricing learning lab/i)).toBeVisible();
    expect(screen.getByText(/authoritative calculations are produced exclusively/i)).toBeVisible();
  });

  it.each([
    ["/guided", "Learn one treaty mechanism at a time"],
    ["/explore", "Build a catalogue-mode treaty scenario"],
    ["/hours-clause", "Test contractual occurrence definitions"],
    ["/compare", "Keep baseline and scenario independent"],
    ["/audit", "Follow every authoritative identity"],
  ])("routes %s to its destination", (path, heading) => {
    renderAt(path);
    expect(screen.getByRole("heading", { level: 1, name: heading })).toBeVisible();
  });

  it("supports keyboard-accessible primary navigation", async () => {
    const user = userEvent.setup();
    renderAt();
    await user.click(screen.getByRole("link", { name: "Hours-Clause Lab" }));
    expect(screen.getByRole("heading", { name: "Test contractual occurrence definitions" })).toBeVisible();
  });

  it("redirects unknown routes to Start", () => {
    renderAt("/unknown");
    expect(screen.getByRole("heading", { name: /see what happened/i })).toBeVisible();
  });
});
