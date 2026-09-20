import type { CatalogueRunRequest } from "../../api/contract";
import type { CT6Problem } from "../../api/contract";

export type CatalogueFormValues = Readonly<{
  simulationId: string;
  sourceMode: "generated" | "supplied";
  simulationSeed: string;
  catalogueVersion: string;
  sourceVersion: string;
  currency: string;
  eventId: string;
  eventTime: string;
  peril: string;
  region: string;
  insuredLoss: string;
  cessionRate: string;
  attachment: string;
  occurrenceLimit: string;
  cededShare: string;
  placementShare: string;
  originalPremium: string;
  reinstatementRate: string;
  settlementMode: "paid_separately" | "deducted_from_settlement";
  responseDetail: "full" | "summary";
}>;

export type CatalogueFormErrors = Partial<Record<keyof CatalogueFormValues, string>>;

export const initialCatalogueForm: CatalogueFormValues = {
  simulationId: "S1",
  sourceMode: "supplied",
  simulationSeed: "",
  catalogueVersion: "teaching-v1",
  sourceVersion: "source-v1",
  currency: "USD",
  eventId: "E1",
  eventTime: "10",
  peril: "wind",
  region: "R1",
  insuredLoss: "45000000",
  cessionRate: "0.10",
  attachment: "10000000",
  occurrenceLimit: "20000000",
  cededShare: "1",
  placementShare: "1",
  originalPremium: "2000000",
  reinstatementRate: "1",
  settlementMode: "paid_separately",
  responseDetail: "full",
};

const serverPathFields: ReadonlyArray<readonly [string, keyof CatalogueFormValues]> = [
  ["simulation.simulation_id", "simulationId"],
  ["simulation.catalogue_source_mode", "sourceMode"],
  ["simulation.simulation_seed", "simulationSeed"],
  ["simulation.catalogue_version", "catalogueVersion"],
  ["simulation.source_version", "sourceVersion"],
  ["event_id", "eventId"],
  ["event_time", "eventTime"],
  ["peril", "peril"],
  ["region", "region"],
  ["reporting_currency", "currency"],
  ["initial_insured_loss", "insuredLoss"],
  ["cession_rate", "cessionRate"],
  ["attachment", "attachment"],
  ["occurrence_limit", "occurrenceLimit"],
  ["ceded_share", "cededShare"],
  ["placement_share", "placementShare"],
  ["original_layer_premium", "originalPremium"],
  ["premium_rate", "reinstatementRate"],
  ["settlement_mode", "settlementMode"],
  ["response_detail", "responseDetail"],
];

export function errorsFromProblem(problem: CT6Problem): CatalogueFormErrors {
  const errors: CatalogueFormErrors = {};
  for (const item of problem.errors) {
    const match = serverPathFields.find(([suffix]) => item.path.endsWith(suffix));
    if (match && errors[match[1]] === undefined) errors[match[1]] = item.message;
  }
  return errors;
}

function text(value: string, field: keyof CatalogueFormValues, errors: CatalogueFormErrors): string {
  const normalized = value.trim();
  if (!normalized) errors[field] = "Required.";
  return normalized;
}

function numeric(
  value: string,
  field: keyof CatalogueFormValues,
  errors: CatalogueFormErrors,
  minimum: number,
  maximum?: number,
): number {
  const parsed = Number(value);
  if (!value.trim() || !Number.isFinite(parsed)) {
    errors[field] = "Enter a finite number.";
  } else if (parsed < minimum || (maximum !== undefined && parsed > maximum)) {
    errors[field] = maximum === undefined
      ? `Enter ${minimum} or more.`
      : `Enter a value from ${minimum} to ${maximum}.`;
  }
  return parsed;
}

export function buildCatalogueRequest(values: CatalogueFormValues): {
  request: CatalogueRunRequest | null;
  errors: CatalogueFormErrors;
} {
  const errors: CatalogueFormErrors = {};
  const simulationId = text(values.simulationId, "simulationId", errors);
  const catalogueVersion = text(values.catalogueVersion, "catalogueVersion", errors);
  const sourceVersion = text(values.sourceVersion, "sourceVersion", errors);
  const currency = text(values.currency, "currency", errors).toUpperCase();
  const eventId = text(values.eventId, "eventId", errors);
  const peril = text(values.peril, "peril", errors);
  const region = text(values.region, "region", errors);
  const eventTime = numeric(values.eventTime, "eventTime", errors, 0);
  const insuredLoss = numeric(values.insuredLoss, "insuredLoss", errors, 0);
  const cessionRate = numeric(values.cessionRate, "cessionRate", errors, 0, 1);
  const attachment = numeric(values.attachment, "attachment", errors, 0);
  const occurrenceLimit = numeric(values.occurrenceLimit, "occurrenceLimit", errors, 0.000001);
  const cededShare = numeric(values.cededShare, "cededShare", errors, 0, 1);
  const placementShare = numeric(values.placementShare, "placementShare", errors, 0, 1);
  const originalPremium = numeric(values.originalPremium, "originalPremium", errors, 0);
  const reinstatementRate = numeric(values.reinstatementRate, "reinstatementRate", errors, 0);

  let simulationSeed: number | null = null;
  if (values.sourceMode === "generated") {
    simulationSeed = numeric(values.simulationSeed, "simulationSeed", errors, 0);
    if (Number.isFinite(simulationSeed) && !Number.isInteger(simulationSeed)) {
      errors.simulationSeed = "Enter a whole-number seed.";
    }
  } else if (values.simulationSeed.trim()) {
    errors.simulationSeed = "Supplied catalogues require a blank seed.";
  }

  if (Object.keys(errors).length) return { request: null, errors };

  const sourceReference = "ct7-explore-form";
  const layerId = "L1";
  const programId = "P1";
  const request: CatalogueRunRequest = {
    api_schema_version: "ct6.0",
    client_request_id: null,
    response_detail: values.responseDetail,
    input: {
      simulation: {
        simulation_id: simulationId,
        trial_count: 1,
        catalogue_source_mode: values.sourceMode,
        catalogue_version: catalogueVersion,
        source_version: sourceVersion,
        simulation_seed: simulationSeed,
        tail_configuration: {
          probability_levels: [0.95, 0.99, 0.995],
          return_periods: [2, 5, 10, 20, 50, 100, 200],
          tvar_levels: [0.99],
        },
        tolerance_profile: {
          absolute_currency_tolerance: 0.000001,
          relative_tolerance: 1e-12,
        },
      },
      trials: [{
        annual_trial_id: 1,
        catalogue_source_id: "CAT-1",
        occurrences: [{
          annual_trial_id: 1,
          event_id: eventId,
          event_time: eventTime,
          event_sequence: 1,
          peril,
          region,
          source_reference: sourceReference,
          trace_reference: "CT7-E1",
          loss_basis: {
            occurrence_id: eventId,
            reporting_currency: currency,
            source_stage_declaration: "insured_loss",
            source_reference: sourceReference,
            initial_insured_loss: insuredLoss,
            ground_up_loss: null,
            components: [{
              component_id: "LC1",
              category: "salvage",
              label: "Declared excluded salvage",
              amount: 0,
              included: false,
              source_reference: sourceReference,
              rule_reference: "F03",
            }],
          },
          inuring_covers: [{
            cover_id: "QS1",
            cover_type: "quota_share",
            order: 1,
            valuation_mode: "calculated_proportional",
            scope_fraction: 1,
            currency,
            description: "Declared inuring quota share",
            source_reference: sourceReference,
            rule_reference: "F05",
            cession_rate: cessionRate,
            occurrence_limit: null,
            aggregate_remaining_before: null,
            recovery_source_id: null,
            supplied_recovery: null,
          }],
        }],
      }],
      program: {
        program_id: programId,
        layers: [{
          layer_id: layerId,
          attachment,
          occurrence_limit: occurrenceLimit,
          ceded_share: cededShare,
          placement_share: placementShare,
          currency,
          description: "Explore Treaty layer",
          source_reference: sourceReference,
          rule_reference: "F11",
        }],
        intentional_gap_acknowledged: false,
        overlap_coordination: "none",
        priority_order: null,
        description: "Single-layer Explore Treaty program",
        source_reference: sourceReference,
        rule_reference: "CT3",
      },
      treaty_terms: {
        program_id: programId,
        layer_terms: [{
          layer_id: layerId,
          original_layer_premium: originalPremium,
          premium_basis_declaration: "payable placed share",
          reinstatement_tranches: [{
            sequence: 1,
            premium_rate: reinstatementRate,
            time_basis: "pro_rata_remaining_term",
            charge_type: "paid",
            source_reference: sourceReference,
            rule_reference: "F30",
          }],
          treaty_term_start: 0,
          treaty_term_end: 365,
          settlement_mode: values.settlementMode,
          capacity_basis: "payable_placed_share",
          source_reference: sourceReference,
          rule_reference: "CT5",
        }],
        source_reference: sourceReference,
        rule_reference: "CT5",
      },
    },
  };
  return { request, errors };
}
