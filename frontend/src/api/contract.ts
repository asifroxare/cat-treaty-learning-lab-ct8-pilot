import type { components } from "./generated/ct6";

export type CatalogueRunRequest = components["schemas"]["CatalogueRunRequest"];
export type HoursRunRequest = components["schemas"]["HoursRunRequest"];
export type CT6Problem = components["schemas"]["CT6ProblemResponse"];
export type CT6ErrorItem = components["schemas"]["CT6ErrorItem"];

export const CT6_SCHEMA_VERSION = "ct6.0" as const;
export const CT6_API_VERSION = "ct6.0.0" as const;

export type RunRequest = CatalogueRunRequest | HoursRunRequest;
