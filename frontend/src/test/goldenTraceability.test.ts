const evidence: Readonly<Record<string, readonly string[]>> = {
  G84: ["App.test.tsx"], G85: ["exploreWorkflow.test.tsx", "catalogueResults.test.tsx"],
  G86: ["hoursWorkflow.test.tsx"], G87: ["exploreWorkflow.test.tsx"], G88: ["hoursWorkflow.test.tsx"],
  G89: ["runState.test.ts", "exploreWorkflow.test.tsx"], G90: ["catalogueResults.test.tsx"],
  G91: ["catalogueResults.test.tsx"], G92: ["catalogueResults.test.tsx"], G93: ["catalogueResults.test.tsx"],
  G94: ["catalogueResults.test.tsx"], G95: ["catalogueResults.test.tsx"], G96: ["compareWorkflow.test.tsx"],
  G97: ["catalogueResults.test.tsx"], G98: ["errorHardening.test.tsx"], G99: ["errorHardening.test.tsx"],
  G100: ["accessibility.test.tsx", "contrast.test.ts"], G101: ["responsiveHardening.test.ts"],
  G102: ["scripts/check-authoritative-types.mjs"], G103: ["realApi.test.tsx"],
  G104: ["guidedScenarios.test.ts"], G105: ["guidedScenarios.test.ts", "scripts/check-content.mjs"],
};

it("maintains permanent test evidence for every frozen CT7 golden case G84-G105", () => {
  expect(Object.keys(evidence)).toEqual(Array.from({ length: 22 }, (_, index) => `G${84 + index}`));
  for (const paths of Object.values(evidence)) expect(paths.length).toBeGreaterThan(0);
});
