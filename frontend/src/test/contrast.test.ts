function luminance(hex: string): number {
  const channels = [1, 3, 5].map((offset) => Number.parseInt(hex.slice(offset, offset + 2), 16) / 255)
    .map((channel) => channel <= 0.03928 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4);
  return 0.2126 * channels[0]! + 0.7152 * channels[1]! + 0.0722 * channels[2]!;
}

function ratio(foreground: string, background: string): number {
  const first = luminance(foreground);
  const second = luminance(background);
  const lighter = Math.max(first, second);
  const darker = Math.min(first, second);
  return (lighter + 0.05) / (darker + 0.05);
}

describe("frozen token contrast", () => {
  it.each([
    ["primary text", "#102a2e", "#f7f5ef"],
    ["muted text", "#466168", "#f7f5ef"],
    ["brand text", "#07584f", "#f7f5ef"],
    ["white button text", "#ffffff", "#086f65"],
    ["white active-nav text", "#ffffff", "#102a2e"],
    ["error text", "#a4382f", "#fffdf8"],
  ])("meets WCAG AA for %s", (_label, foreground, background) => {
    expect(ratio(foreground, background)).toBeGreaterThanOrEqual(4.5);
  });
});
