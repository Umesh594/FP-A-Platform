import { BrowserRouter, Routes, Route } from "react-router-dom";
import { useEffect } from "react";
import { AppLayout } from "@/components/AppLayout";
import { SocketProvider } from "@/contexts/SocketContext";
import { useAppStore } from "@/stores/appStore";
import PortfolioDashboard from "@/pages/PortfolioDashboard";
import CompanyDetail from "@/pages/CompanyDetail";
import ScenarioBuilder from "@/pages/ScenarioBuilder";
import KPIScorecard from "@/pages/KPIScorecard";
import ReportsExports from "@/pages/ReportsExports";
import EmailCenter from "@/pages/EmailCenter";

function ThemeInit() {
  const { theme } = useAppStore();
  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
  }, [theme]);
  return null;
}

export default function App() {
  return (
    <BrowserRouter>
      <ThemeInit />
      <SocketProvider>
        <AppLayout>
          <Routes>
            <Route path="/" element={<PortfolioDashboard />} />
           <Route path="/company/:id" element={<CompanyDetail />} />
<Route path="/company" element={<CompanyDetail />} />
            <Route path="/scenarios" element={<ScenarioBuilder />} />
            <Route path="/kpis" element={<KPIScorecard />} />
            <Route path="/reports" element={<ReportsExports />} />
            <Route path="/emails" element={<EmailCenter />} />
          </Routes>
        </AppLayout>
      </SocketProvider>
    </BrowserRouter>
  );
}