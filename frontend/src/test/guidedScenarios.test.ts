import { guidedExperiments } from "../scenarios/guided";
import { resolveEvidence, validateNeutralContent } from "../scenarios/evidence";
import { ct6SuccessFixture, hoursSuccessFixture } from "./fixtures/ct6Success";

describe("guided scenario catalogue and learning integrity", () => {
  it("contains seven versioned complete controlled experiments", () => {
    expect(guidedExperiments.map((item) => item.id)).toEqual(["E01", "E02", "E03", "E04", "E05", "E06", "E07"]);
    for (const experiment of guidedExperiments) {
      expect(experiment.version).toBe("1.0");
      expect(experiment.controlledFields.length).toBeGreaterThan(0);
      expect(experiment.baseline.request.api_schema_version).toBe("ct6.0");
      expect(experiment.scenario.request.api_schema_version).toBe("ct6.0");
      expect(() => validateNeutralContent(experiment.takeaway)).not.toThrow();
    }
  });

  it("changes only the declared learning mechanism for representative fixtures", () => {
    const shares = guidedExperiments.find((item) => item.id === "E03")!;
    if (shares.baseline.mode !== "catalogue" || shares.scenario.mode !== "catalogue") throw new Error("E03 mode mismatch");
    expect(shares.baseline.request.input.program.layers[0]?.placement_share).toBe(1);
    expect(shares.scenario.request.input.program.layers[0]?.placement_share).toBe(0.75);
    const hours = guidedExperiments.find((item) => item.id === "E07")!;
    expect(hours.baseline.mode).toBe("hours_clause");
    expect(hours.scenario.mode).toBe("hours_clause");
  });

  it("fails closed for missing evidence and prohibited recommendation language", () => {
    expect(resolveEvidence(ct6SuccessFixture(), { statement: "Inspect the returned field.", evidencePaths: ["missing.path"] })).toBe(false);
    expect(() => validateNeutralContent({ statement: "This is the recommended election.", evidencePaths: ["identity.ct5_result_hash"] })).toThrow(/prohibited/i);
    expect(resolveEvidence(hoursSuccessFixture(), guidedExperiments[6]!.takeaway)).toBe(true);
  });
});
