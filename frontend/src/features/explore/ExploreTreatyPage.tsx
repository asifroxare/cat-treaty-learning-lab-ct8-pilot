import type { ChangeEvent, ReactNode } from "react";

import type { CatalogueFormValues } from "./catalogueForm";
import { CatalogueResults } from "../results/CatalogueResults";
import { RunErrorPanel } from "../../components/RunErrorPanel";
import { useCatalogueRun } from "./useCatalogueRun";
import "./ExploreTreatyPage.css";

interface FieldProps {
  id: keyof CatalogueFormValues;
  label: string;
  hint: string;
  error?: string;
  children: ReactNode;
}

function Field({ id, label, hint, error, children }: FieldProps) {
  const hintId = `${id}-hint`;
  const errorId = `${id}-error`;
  return (
    <div className="form-field">
      <label htmlFor={id}>{label}</label>
      {children}
      <span className="field-hint" id={hintId}>{hint}</span>
      {error && <span className="field-error" id={errorId} role="alert">{error}</span>}
    </div>
  );
}

export function ExploreTreatyPage() {
  const run = useCatalogueRun();
  const disabled = run.executionState === "submitting";
  const describedBy = (field: keyof CatalogueFormValues) =>
    `${field}-hint${run.errors[field] ? ` ${field}-error` : ""}`;
  const input = (field: keyof CatalogueFormValues) => ({
    id: field,
    name: field,
    value: run.values[field],
    disabled,
    "aria-invalid": Boolean(run.errors[field]),
    "aria-describedby": describedBy(field),
    onChange: (event: ChangeEvent<HTMLInputElement>) => run.setField(field, event.target.value as never),
  });

  return (
    <section className="explore-page" aria-labelledby="explore-title">
      <header className="explore-heading">
        <div>
          <p className="page-eyebrow">Explore Treaty</p>
          <h1 id="explore-title">Build a catalogue-mode treaty scenario</h1>
          <p className="page-lede">Declare the source loss, inuring cover, Cat XL layer and annual-capacity terms. CT6 remains the sole calculation authority.</p>
        </div>
        <div className={`run-state run-state--${run.executionState}`} aria-live="polite">
          <span>Run state</span>
          <strong>{run.executionState.replace("_", " ")}</strong>
        </div>
      </header>

      <form onSubmit={(event) => { event.preventDefault(); void run.submit(); }} noValidate>
        <fieldset disabled={disabled}>
          <legend>Simulation and provenance</legend>
          <div className="form-grid">
            <Field id="simulationId" label="Simulation ID" hint="Provenance identifier; required." error={run.errors.simulationId}>
              <input {...input("simulationId")} />
            </Field>
            <Field id="sourceMode" label="Catalogue source" hint="Generated requires a seed; supplied requires none." error={run.errors.sourceMode}>
              <select id="sourceMode" value={run.values.sourceMode} aria-describedby={describedBy("sourceMode")} onChange={(event) => run.setField("sourceMode", event.target.value as CatalogueFormValues["sourceMode"])}>
                <option value="supplied">Supplied</option><option value="generated">Generated</option>
              </select>
            </Field>
            <Field id="simulationSeed" label="Simulation seed" hint="Whole number for generated catalogues; blank for supplied." error={run.errors.simulationSeed}>
              <input {...input("simulationSeed")} inputMode="numeric" />
            </Field>
            <Field id="catalogueVersion" label="Catalogue version" hint="Version of the explicit occurrence catalogue." error={run.errors.catalogueVersion}>
              <input {...input("catalogueVersion")} />
            </Field>
            <Field id="sourceVersion" label="Source version" hint="Version of the declared source data." error={run.errors.sourceVersion}>
              <input {...input("sourceVersion")} />
            </Field>
            <Field id="responseDetail" label="Response detail" hint="Full may be rejected when row limits are exceeded." error={run.errors.responseDetail}>
              <select id="responseDetail" value={run.values.responseDetail} aria-describedby={describedBy("responseDetail")} onChange={(event) => run.setField("responseDetail", event.target.value as CatalogueFormValues["responseDetail"])}>
                <option value="full">Full</option><option value="summary">Summary</option>
              </select>
            </Field>
          </div>
        </fieldset>

        <fieldset disabled={disabled}>
          <legend>Occurrence loss basis and inuring order</legend>
          <div className="form-grid">
            <Field id="eventId" label="Event ID" hint="Unique within this one-trial teaching catalogue." error={run.errors.eventId}><input {...input("eventId")} /></Field>
            <Field id="eventTime" label="Event time" hint="Day within the treaty term; 0 or greater." error={run.errors.eventTime}><input {...input("eventTime")} inputMode="decimal" /></Field>
            <Field id="peril" label="Peril" hint="Declared occurrence peril." error={run.errors.peril}><input {...input("peril")} /></Field>
            <Field id="region" label="Region" hint="Declared occurrence region." error={run.errors.region}><input {...input("region")} /></Field>
            <Field id="currency" label="Reporting currency" hint="Shared by the loss, inuring cover and layer." error={run.errors.currency}><input {...input("currency")} maxLength={3} /></Field>
            <Field id="insuredLoss" label="Initial insured loss" hint="Currency amount at the declared insured-loss stage." error={run.errors.insuredLoss}><input {...input("insuredLoss")} inputMode="decimal" /></Field>
            <Field id="cessionRate" label="Inuring quota-share cession" hint="Contractual decimal from 0 to 1; applied by CT2." error={run.errors.cessionRate}><input {...input("cessionRate")} inputMode="decimal" /></Field>
          </div>
        </fieldset>

        <fieldset disabled={disabled}>
          <legend>Cat XL layer and annual capacity</legend>
          <div className="form-grid">
            <Field id="attachment" label="Occurrence attachment" hint="Currency amount; 0 or greater." error={run.errors.attachment}><input {...input("attachment")} inputMode="decimal" /></Field>
            <Field id="occurrenceLimit" label="Occurrence limit" hint="Positive currency amount." error={run.errors.occurrenceLimit}><input {...input("occurrenceLimit")} inputMode="decimal" /></Field>
            <Field id="cededShare" label="Ceded share" hint="Contractual decimal from 0 to 1." error={run.errors.cededShare}><input {...input("cededShare")} inputMode="decimal" /></Field>
            <Field id="placementShare" label="Placement share" hint="Placed decimal from 0 to 1; kept separate from ceded share." error={run.errors.placementShare}><input {...input("placementShare")} inputMode="decimal" /></Field>
            <Field id="originalPremium" label="Original layer premium" hint="Premium on the payable placed-share basis." error={run.errors.originalPremium}><input {...input("originalPremium")} inputMode="decimal" /></Field>
            <Field id="reinstatementRate" label="Paid reinstatement rate" hint="Rate for one pro-rata remaining-term tranche." error={run.errors.reinstatementRate}><input {...input("reinstatementRate")} inputMode="decimal" /></Field>
            <Field id="settlementMode" label="Settlement mode" hint="Changes presentation of premium payment, not contractual recovery." error={run.errors.settlementMode}>
              <select id="settlementMode" value={run.values.settlementMode} aria-describedby={describedBy("settlementMode")} onChange={(event) => run.setField("settlementMode", event.target.value as CatalogueFormValues["settlementMode"])}>
                <option value="paid_separately">Paid separately</option><option value="deducted_from_settlement">Deducted from settlement</option>
              </select>
            </Field>
          </div>
        </fieldset>

        <div className="run-actions">
          <button type="submit" disabled={disabled}>{disabled ? "Running CT6…" : "Run treaty scenario"}</button>
          <p>One explicit trial · one event · one inuring cover · one Cat XL layer</p>
        </div>
      </form>

      {run.executionState === "schema_error" && Object.keys(run.errors).length > 0 && (
        <section className="run-message run-message--error" aria-labelledby="validation-title">
          <h2 id="validation-title">Correct the highlighted request fields</h2>
          <p>The browser only checks request completeness and shape. CT6 remains the authoritative treaty validator.</p>
        </section>
      )}
      {(run.executionState !== "schema_error" || Object.keys(run.errors).length === 0) && <RunErrorPanel state={run.executionState} problem={run.problem} />}
      {run.priorSuccess && (
        <>
          <section className={`run-message ${run.freshness === "stale" ? "run-message--stale" : "run-message--success"}`} aria-labelledby="result-status-title">
            <h2 id="result-status-title">{run.freshness === "stale" ? "Previous result — inputs changed" : "Authoritative run completed"}</h2>
            <p>Request ID: <code>{run.priorSuccess.requestId}</code></p>
            <p>{run.freshness === "stale" ? "Run the edited request before treating it as current." : "Every value below comes from the completed CT6 response."}</p>
          </section>
          <CatalogueResults data={run.priorSuccess.data} freshness={run.freshness} />
        </>
      )}
    </section>
  );
}
