import type { HoursRunRequest } from "../../api/contract";
import { buildCatalogueRequest, initialCatalogueForm } from "../explore/catalogueForm";

export type ElectionMethod = HoursRunRequest["input"]["terms"]["selected_election_method"];

export interface HoursFormValues {
  scenarioId: string;
  sourceVersion: string;
  hoursDuration: string;
  treatyStart: string;
  treatyEnd: string;
  permittedPeril: string;
  permittedRegion: string;
  causalLinkRequired: boolean;
  selectedMethod: ElectionMethod;
  manualCandidateSetId: string;
  component1Id: string;
  component1Loss: string;
  component1Time: string;
  component1Cause: string;
  component2Id: string;
  component2Loss: string;
  component2Time: string;
  component2Cause: string;
  responseDetail: "full" | "summary";
}

export type HoursFormErrors = Partial<Record<keyof HoursFormValues, string>>;

export const initialHoursForm: HoursFormValues = {
  scenarioId: "H1", sourceVersion: "hours-v1", hoursDuration: "72",
  treatyStart: "0", treatyEnd: "365", permittedPeril: "wind", permittedRegion: "R1",
  causalLinkRequired: true, selectedMethod: "maximum_subject_loss", manualCandidateSetId: "",
  component1Id: "C1", component1Loss: "20000000", component1Time: "10", component1Cause: "storm",
  component2Id: "C2", component2Loss: "20000000", component2Time: "100", component2Cause: "storm",
  responseDetail: "full",
};

function required(value: string, field: keyof HoursFormValues, errors: HoursFormErrors): string {
  const result = value.trim();
  if (!result) errors[field] = "Required.";
  return result;
}

function numeric(value: string, field: keyof HoursFormValues, errors: HoursFormErrors, positive = false): number {
  const result = Number(value);
  if (!value.trim() || !Number.isFinite(result)) errors[field] = "Enter a finite number.";
  else if (positive ? result <= 0 : result < 0) errors[field] = positive ? "Enter a value greater than zero." : "Enter zero or more.";
  return result;
}

export function buildHoursRequest(values: HoursFormValues): { request: HoursRunRequest | null; errors: HoursFormErrors } {
  const errors: HoursFormErrors = {};
  const scenarioId = required(values.scenarioId, "scenarioId", errors);
  const sourceVersion = required(values.sourceVersion, "sourceVersion", errors);
  const permittedPeril = required(values.permittedPeril, "permittedPeril", errors);
  const permittedRegion = required(values.permittedRegion, "permittedRegion", errors);
  const hoursDuration = numeric(values.hoursDuration, "hoursDuration", errors, true);
  const treatyStart = numeric(values.treatyStart, "treatyStart", errors);
  const treatyEnd = numeric(values.treatyEnd, "treatyEnd", errors, true);
  if (Number.isFinite(treatyStart) && Number.isFinite(treatyEnd) && treatyEnd <= treatyStart) errors.treatyEnd = "Treaty end must be after treaty start.";
  const component1Id = required(values.component1Id, "component1Id", errors);
  const component2Id = required(values.component2Id, "component2Id", errors);
  if (component1Id && component1Id === component2Id) errors.component2Id = "Component IDs must be unique.";
  const component1Loss = numeric(values.component1Loss, "component1Loss", errors);
  const component2Loss = numeric(values.component2Loss, "component2Loss", errors);
  const component1Time = numeric(values.component1Time, "component1Time", errors);
  const component2Time = numeric(values.component2Time, "component2Time", errors);
  const component1Cause = required(values.component1Cause, "component1Cause", errors);
  const component2Cause = required(values.component2Cause, "component2Cause", errors);
  const manual = values.selectedMethod === "manual";
  const manualCandidateSetId = values.manualCandidateSetId.trim();
  if (manual && !manualCandidateSetId) errors.manualCandidateSetId = "Select or enter a candidate-set ID for manual election.";
  if (!manual && manualCandidateSetId) errors.manualCandidateSetId = "A manual candidate ID is allowed only for manual election.";
  if (Object.keys(errors).length) return { request: null, errors };

  const catalogue = buildCatalogueRequest(initialCatalogueForm).request;
  if (!catalogue) throw new Error("Frozen CT7 program-source template is invalid");
  const programSource = catalogue.input.trials[0]?.occurrences[0];
  if (!programSource) throw new Error("Frozen CT7 program-source occurrence is missing");
  const sourceReference = "ct7-hours-form";
  return {
    errors,
    request: {
      api_schema_version: "ct6.0", client_request_id: null, response_detail: values.responseDetail,
      input: {
        scenario_id: scenarioId, source_version: sourceVersion, source_reference: sourceReference,
        components: [
          { component_id: component1Id, subject_loss: component1Loss, timestamp: component1Time, peril: permittedPeril, region: permittedRegion, causal_event_id: component1Cause, source_reference: sourceReference },
          { component_id: component2Id, subject_loss: component2Loss, timestamp: component2Time, peril: permittedPeril, region: permittedRegion, causal_event_id: component2Cause, source_reference: sourceReference },
        ],
        terms: {
          treaty_term_start: treatyStart, treaty_term_end: treatyEnd, hours_duration: hoursDuration,
          permitted_perils: [permittedPeril], permitted_regions: [permittedRegion], causal_link_required: values.causalLinkRequired,
          authorized_election_methods: ["earliest_valid_window", "maximum_subject_loss", "maximum_contractual_recovery", "manual"],
          selected_election_method: values.selectedMethod, manual_candidate_set_id: manual ? manualCandidateSetId : null,
          rule_reference: "CT4-hours",
        },
        program_source: programSource, program: catalogue.input.program, treaty_terms: catalogue.input.treaty_terms,
        tail_configuration: catalogue.input.simulation.tail_configuration,
        tolerance_profile: catalogue.input.simulation.tolerance_profile,
      },
    },
  };
}
