import { buildHoursRequest, initialHoursForm } from "../features/hours/hoursForm";

describe("hours-clause request builder", () => {
  it("serializes timestamped components and all authorized election methods", () => {
    const built = buildHoursRequest(initialHoursForm);
    expect(built.errors).toEqual({});
    expect(built.request).toMatchObject({
      api_schema_version: "ct6.0",
      input: {
        scenario_id: "H1",
        components: [{ component_id: "C1", timestamp: 10 }, { component_id: "C2", timestamp: 100 }],
        terms: { hours_duration: 72, selected_election_method: "maximum_subject_loss", manual_candidate_set_id: null },
      },
    });
    expect(built.request?.input.terms.authorized_election_methods).toEqual([
      "earliest_valid_window", "maximum_subject_loss", "maximum_contractual_recovery", "manual",
    ]);
  });

  it("requires a candidate-set ID only for manual election", () => {
    const missing = buildHoursRequest({ ...initialHoursForm, selectedMethod: "manual" });
    expect(missing.request).toBeNull();
    expect(missing.errors.manualCandidateSetId).toBeDefined();
    const valid = buildHoursRequest({ ...initialHoursForm, selectedMethod: "manual", manualCandidateSetId: "SET-001" });
    expect(valid.request?.input.terms.manual_candidate_set_id).toBe("SET-001");
    const forbidden = buildHoursRequest({ ...initialHoursForm, manualCandidateSetId: "SET-001" });
    expect(forbidden.errors.manualCandidateSetId).toBeDefined();
  });

  it("rejects duplicate component IDs and invalid treaty bounds", () => {
    const built = buildHoursRequest({ ...initialHoursForm, component2Id: "C1", treatyEnd: "0" });
    expect(built.request).toBeNull();
    expect(built.errors).toMatchObject({ component2Id: expect.any(String), treatyEnd: expect.any(String) });
  });
});
