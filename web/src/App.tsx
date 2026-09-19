import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom"

import { AppShell } from "@/components/app-shell"
import { ExpenditurePage } from "@/pages/expenditure-page"
import { MappingsPage } from "@/pages/mappings-page"
import { OverviewPage } from "@/pages/overview-page"
import { TransactionsPage } from "@/pages/transactions-page"

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<OverviewPage />} />
          <Route path="transactions" element={<TransactionsPage />} />
          <Route path="transactions/:id" element={<ExpenditurePage />} />
          <Route path="mappings" element={<MappingsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
