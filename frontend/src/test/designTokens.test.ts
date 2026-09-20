import tokens from "../styles/tokens.css?raw";

describe("design-token contract", () => {
  it("defines semantic color, typography, spacing and focus tokens", () => {
    for (const token of [
      "--color-brand",
      "--color-danger",
      "--color-focus",
      "--font-display",
      "--font-mono",
      "--space-4",
      "--content-max",
    ]) {
      expect(tokens).toContain(token);
    }
  });
});
