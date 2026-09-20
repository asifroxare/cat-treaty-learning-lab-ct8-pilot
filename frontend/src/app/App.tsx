import { Navigate, Route, Routes } from "react-router-dom";

import type { CT6Client } from "../api/client";
import { AppShell } from "../components/AppShell";
import { FoundationPage } from "../components/FoundationPage";
import { ExploreTreatyPage } from "../features/explore/ExploreTreatyPage";
import { CatalogueRunProvider } from "../features/explore/useCatalogueRun";
import { AuditTrailPage } from "../features/audit/AuditTrailPage";
import { HomePage } from "../features/home/HomePage";

const routeContent = {
  guided: {
    eyebrow: "Guided Lab",
    title: "Learn one treaty mechanism at a time",
    description: "Controlled experiments will connect each input change to CT6 evidence and a neutral takeaway.",
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
} as const;

export function App({ client }: { client?: CT6Client }) {
  return (
    <CatalogueRunProvider client={client}>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<HomePage />} />
          <Route path="guided" element={<FoundationPage {...routeContent.guided} />} />
          <Route path="explore" element={<ExploreTreatyPage />} />
          <Route path="hours-clause" element={<FoundationPage {...routeContent.hours} />} />
          <Route path="compare" element={<FoundationPage {...routeContent.compare} />} />
          <Route path="audit" element={<AuditTrailPage />} />
          <Route path="*" element={<Navigate replace to="/" />} />
        </Route>
      </Routes>
    </CatalogueRunProvider>
  );
}
