import { Navigate, Route, Routes } from "react-router-dom";

import type { CT6Client } from "../api/client";
import { AppShell } from "../components/AppShell";
import { ExploreTreatyPage } from "../features/explore/ExploreTreatyPage";
import { CatalogueRunProvider } from "../features/explore/useCatalogueRun";
import { AuditTrailPage } from "../features/audit/AuditTrailPage";
import { HoursClausePage } from "../features/hours/HoursClausePage";
import { HoursRunProvider } from "../features/hours/useHoursRun";
import { HomePage } from "../features/home/HomePage";
import { GuidedLabPage } from "../features/guided/GuidedLabPage";
import { ComparePage } from "../features/compare/ComparePage";

export function App({ client }: { client?: CT6Client }) {
  return (
    <CatalogueRunProvider client={client}>
      <HoursRunProvider client={client}>
       <Routes>
        <Route element={<AppShell />}>
          <Route index element={<HomePage />} />
          <Route path="guided" element={<GuidedLabPage client={client} />} />
          <Route path="explore" element={<ExploreTreatyPage />} />
          <Route path="hours-clause" element={<HoursClausePage />} />
          <Route path="compare" element={<ComparePage client={client} />} />
          <Route path="audit" element={<AuditTrailPage />} />
          <Route path="*" element={<Navigate replace to="/" />} />
        </Route>
       </Routes>
      </HoursRunProvider>
    </CatalogueRunProvider>
  );
}
