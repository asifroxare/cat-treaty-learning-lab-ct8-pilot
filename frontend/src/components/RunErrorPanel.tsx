import { useEffect, useRef } from "react";

import type { CT6Problem } from "../api/contract";
import type { ExecutionState } from "../api/runState";

const publicMessages: Record<Exclude<ExecutionState, "editing" | "submitting" | "success">, { title: string; message: string }> = {
  schema_error: { title: "The request needs correction", message: "Review the highlighted fields and CT6 path evidence. No result was created." },
  domain_error: { title: "The treaty terms are not valid", message: "Review the returned rule references. The lab will not invent replacement terms." },
  contract_blocked: { title: "The contract blocks this run", message: "Review the returned election or geometry evidence. No partial recovery is displayed." },
  too_large: { title: "The full response would be too large", message: "Select summary response detail and submit again. The lab never downgrades a request automatically." },
  server_error: { title: "The CT6 service could not complete the run", message: "Retry later. No internal path, stack trace or partial result is displayed." },
  offline: { title: "The CT6 service is unavailable", message: "Check the API connection and retry. No simulated fallback result was created." },
};

export function RunErrorPanel({ state, problem }: { state: ExecutionState; problem: CT6Problem | null }) {
  const heading = useRef<HTMLHeadingElement>(null);
  const content = state in publicMessages
    ? publicMessages[state as keyof typeof publicMessages]
    : null;
  useEffect(() => { if (content) heading.current?.focus(); }, [content, state]);
  if (!content) return null;
  return (
    <section className="run-message run-message--error" role="alert" aria-labelledby={`${state}-title`}>
      <h2 id={`${state}-title`} ref={heading} tabIndex={-1}>{content.title}</h2>
      <p>{content.message}</p>
      {problem && <p><strong>Code:</strong> {problem.code} · <strong>Request:</strong> {problem.request_id}</p>}
      {problem && problem.errors.length > 0 && <ul>{problem.errors.map((item, index) => <li key={`${item.path}-${item.code}-${index}`}>{item.message} <small>{item.path} · {item.rule_reference}</small></li>)}</ul>}
    </section>
  );
}
