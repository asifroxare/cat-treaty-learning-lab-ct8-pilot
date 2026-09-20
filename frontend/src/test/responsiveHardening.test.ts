import shellCss from "../components/AppShell.css?raw";
import exploreCss from "../features/explore/ExploreTreatyPage.css?raw";
import globalCss from "../styles/global.css?raw";

describe("responsive and reduced-motion contract", () => {
  it("retains the 320px floor, reduced motion and forced-colors safeguards", () => {
    expect(globalCss).toContain("min-width: 320px");
    expect(globalCss).toContain("prefers-reduced-motion: reduce");
    expect(globalCss).toContain("forced-colors: active");
  });

  it("collapses shell and dense form layouts for narrow screens", () => {
    expect(shellCss).toContain("@media (max-width: 48rem)");
    expect(exploreCss).toContain("@media (max-width: 620px)");
    expect(exploreCss).toMatch(/grid-template-columns:\s*1fr/);
  });
});
