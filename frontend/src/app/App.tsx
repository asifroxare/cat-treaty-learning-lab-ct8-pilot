import { Navigate, Route, Routes } from "react-router-dom";

import { AppShell } from "../components/AppShell";
import { FoundationPage } from "../components/FoundationPage";
import { HomePage } from "../features/home/HomePage";

const routeContent = {
  guided: {
    eyebrow: "Guided Lab",
    title: "Learn one treaty mechanism at a time",
    description: "Controlled experiments will connect each input change to CT6 evidence and a neutral takeaway.",
  },
  explore: {
    eyebrow: "Explore Treaty",
    title: "Build a catalogue-mode treaty scenario",
    description: "The next checkpoint will add strict request builders for loss stages, program terms and annual capacity.",
  },
  hours: {
    eyebrow: "Hours-Clause Lab",
    title: "Test contractual occurrence definitions",
    description: "Candidate windows, exclusions and elections will remain visible before any selected occurrence reaches CT5.",
  },
  compare: {
    eyebrow: "Compare",
    title: "Keep baseline and scenario independent",
    description: "Two complete CT6 responses will appear side by side without client-calculated deltas or rankings.",
  },
  audit: {
    eyebrow: "Audit Trail",
    title: "Follow every authoritative identity",
    description: "Request IDs, CT4/CT5 hashes, warnings, reconciliations and rule references will be available here.",
  },
} as const;

export function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<HomePage />} />
        <Route path="guided" element={<FoundationPage {...routeContent.guided} />} />
        <Route path="explore" element={<FoundationPage {...routeContent.explore} />} />
        <Route path="hours-clause" element={<FoundationPage {...routeContent.hours} />} />
        <Route path="compare" element={<FoundationPage {...routeContent.compare} />} />
        <Route path="audit" element={<FoundationPage {...routeContent.audit} />} />
        <Route path="*" element={<Navigate replace to="/" />} />
      </Route>
    </Routes>
  );
}
