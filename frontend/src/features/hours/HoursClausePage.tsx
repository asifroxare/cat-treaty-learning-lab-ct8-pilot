import type { ChangeEvent, ReactNode } from "react";

import type { HoursFormValues } from "./hoursForm";
import { RunErrorPanel } from "../../components/RunErrorPanel";
import { HoursClauseResults } from "./HoursClauseResults";
import { useHoursRun } from "./useHoursRun";
import "../explore/ExploreTreatyPage.css";
import "../results/CatalogueResults.css";
import "./HoursClausePage.css";

function Field({ id, label, hint, error, children }: { id: keyof HoursFormValues; label: string; hint: string; error?: string; children: ReactNode }) {
  return <div className="form-field"><label htmlFor={id}>{label}</label>{children}<span className="field-hint" id={`${id}-hint`}>{hint}</span>{error && <span className="field-error" id={`${id}-error`} role="alert">{error}</span>}</div>;
}

export function HoursClausePage() {
  const run = useHoursRun();
  const disabled = run.executionState === "submitting";
  const describedBy = (field: keyof HoursFormValues) => `${field}-hint${run.errors[field] ? ` ${field}-error` : ""}`;
  const input = (field: keyof HoursFormValues) => ({
    id: field, name: field, value: String(run.values[field]), disabled,
    "aria-invalid": Boolean(run.errors[field]), "aria-describedby": describedBy(field),
    onChange: (event: ChangeEvent<HTMLInputElement>) => run.setField(field, event.target.value as never),
  });

  return (
    <section className="explore-page hours-page" aria-labelledby="hours-title">
      <header className="explore-heading"><div><p className="page-eyebrow">Hours-Clause Lab</p><h1 id="hours-title">Test contractual occurrence definitions</h1><p className="page-lede">Generate candidate windows first, preserve exclusion reasons, and elect only from the contractually valid set.</p></div><div className={`run-state run-state--${run.executionState}`} aria-live="polite"><span>Run state</span><strong>{run.executionState.replace("_", " ")}</strong></div></header>
      <form onSubmit={(event) => { event.preventDefault(); void run.submit(); }} noValidate>
        <fieldset disabled={disabled}><legend>Scenario and treaty hours</legend><div className="form-grid">
          <Field id="scenarioId" label="Scenario ID" hint="Bounded teaching-scenario identifier." error={run.errors.scenarioId}><input {...input("scenarioId")} /></Field>
          <Field id="sourceVersion" label="Source version" hint="Provenance version for timestamped components." error={run.errors.sourceVersion}><input {...input("sourceVersion")} /></Field>
          <Field id="hoursDuration" label="Hours duration" hint="Positive contractual window duration." error={run.errors.hoursDuration}><input {...input("hoursDuration")} inputMode="decimal" /></Field>
          <Field id="treatyStart" label="Treaty-term start" hint="Non-negative time boundary." error={run.errors.treatyStart}><input {...input("treatyStart")} inputMode="decimal" /></Field>
          <Field id="treatyEnd" label="Treaty-term end" hint="Must be later than treaty start." error={run.errors.treatyEnd}><input {...input("treatyEnd")} inputMode="decimal" /></Field>
          <Field id="permittedPeril" label="Permitted peril" hint="Components use this declared peril." error={run.errors.permittedPeril}><input {...input("permittedPeril")} /></Field>
          <Field id="permittedRegion" label="Permitted region" hint="Components use this declared region." error={run.errors.permittedRegion}><input {...input("permittedRegion")} /></Field>
          <div className="form-field checkbox-field"><label><input type="checkbox" checked={run.values.causalLinkRequired} disabled={disabled} onChange={(event) => run.setField("causalLinkRequired", event.target.checked)} /> Require common causal event</label><span className="field-hint">Contractual causal-link admissibility control.</span></div>
        </div></fieldset>

        <fieldset disabled={disabled}><legend>Timestamped loss components</legend><div className="component-grid">
          <ComponentFields number="1" input={input} errors={run.errors} />
          <ComponentFields number="2" input={input} errors={run.errors} />
        </div></fieldset>

        <fieldset disabled={disabled}><legend>Contractual election</legend><div className="form-grid">
          <Field id="selectedMethod" label="Selected election method" hint="All four methods are contractually authorized in this teaching scenario." error={run.errors.selectedMethod}><select id="selectedMethod" value={run.values.selectedMethod} aria-describedby={describedBy("selectedMethod")} onChange={(event) => run.setField("selectedMethod", event.target.value as HoursFormValues["selectedMethod"])}><option value="earliest_valid_window">Earliest valid window</option><option value="maximum_subject_loss">Maximum subject loss</option><option value="maximum_contractual_recovery">Maximum contractual recovery</option><option value="manual">Manual valid candidate set</option></select></Field>
          <Field id="manualCandidateSetId" label="Manual candidate-set ID" hint="Required only when manual election is selected." error={run.errors.manualCandidateSetId}><input {...input("manualCandidateSetId")} disabled={disabled || run.values.selectedMethod !== "manual"} /></Field>
          <Field id="responseDetail" label="Response detail" hint="Election evidence remains in full and summary responses." error={run.errors.responseDetail}><select id="responseDetail" value={run.values.responseDetail} aria-describedby={describedBy("responseDetail")} onChange={(event) => run.setField("responseDetail", event.target.value as HoursFormValues["responseDetail"])}><option value="full">Full</option><option value="summary">Summary</option></select></Field>
        </div></fieldset>
        <div className="run-actions"><button type="submit" disabled={disabled}>{disabled ? "Running CT6…" : "Generate and elect occurrence"}</button><p>Two timestamped components · validated program source · one annual trial</p></div>
      </form>

      {run.executionState === "schema_error" && Object.keys(run.errors).length > 0 && <section className="run-message run-message--error"><h2>Correct the highlighted scenario fields</h2><p>CT6 remains the authoritative contractual validator.</p></section>}
      {Object.keys(run.errors).length === 0 && <RunErrorPanel state={run.executionState} problem={run.problem} />}
      {run.priorSuccess && <><section className={`run-message ${run.freshness === "stale" ? "run-message--stale" : "run-message--success"}`}><h2>{run.freshness === "stale" ? "Previous result — inputs changed" : "Authoritative hours-clause run completed"}</h2><p>Request ID: <code>{run.priorSuccess.requestId}</code></p></section><HoursClauseResults data={run.priorSuccess.data} freshness={run.freshness} /></>}
    </section>
  );
}

function ComponentFields({ number, input, errors }: { number: "1" | "2"; input: (field: keyof HoursFormValues) => Record<string, unknown>; errors: Partial<Record<keyof HoursFormValues, string>> }) {
  const id = `component${number}Id` as keyof HoursFormValues;
  const loss = `component${number}Loss` as keyof HoursFormValues;
  const time = `component${number}Time` as keyof HoursFormValues;
  const cause = `component${number}Cause` as keyof HoursFormValues;
  return <div className="component-card"><h2>Component {number}</h2><Field id={id} label="Component ID" hint="Unique component identifier." error={errors[id]}><input {...input(id)} /></Field><Field id={loss} label="Subject loss" hint="Non-negative authoritative source amount." error={errors[loss]}><input {...input(loss)} inputMode="decimal" /></Field><Field id={time} label="Timestamp" hint="Time used for candidate-window generation." error={errors[time]}><input {...input(time)} inputMode="decimal" /></Field><Field id={cause} label="Causal event ID" hint="Used when causal linkage is required." error={errors[cause]}><input {...input(cause)} /></Field></div>;
}
