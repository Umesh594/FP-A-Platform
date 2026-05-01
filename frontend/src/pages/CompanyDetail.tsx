import { useParams, useNavigate } from "react-router-dom";
import { useMemo, useEffect } from "react";
import { useAppStore } from "@/stores/appStore";
import {
  useFinancialHistory,
  useFinancialForecast,
  useInitiatives,
  useDrivers,
  useVariance,
} from "@/hooks/useApi";
import type { CompanyId } from "@/stores/appStore";
import type { MonthlyFinancial } from "@/components/company/FinancialModelTable";
import { FinancialModelTable } from "@/components/company/FinancialModelTable";
import { RevenueExpenseCharts } from "@/components/company/RevenueExpenseCharts";
import { ScenarioComparison } from "@/components/company/ScenarioComparison";
import { VarianceAnalysis } from "@/components/company/VarianceAnalysis";
import { DriverDashboard } from "@/components/company/DriverDashboard";
import { InitiativeTracker } from "@/components/company/InitiativeTracker";
import { CompanySelector } from "@/components/company/CompanySelector";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Loader2 } from "lucide-react";

export default function CompanyDetail() {
  const { id } = useParams();
const navigate = useNavigate();
const { companies, setSelectedCompany } = useAppStore();

// ✅ always derive from URL first
const companyId = id as CompanyId | undefined;

// ✅ fallback to first company if URL missing/invalid
const company =
  companies.find((c) => c.id === companyId) || companies[0];

// ✅ sync Zustand (IMPORTANT)
useEffect(() => {
  if (company?.id) {
    setSelectedCompany(company.id);
  }
}, [company?.id, setSelectedCompany]);

// ❌ prevent blank page
if (!company) return <div>Loading...</div>;

const apiId: number | null = company.apiId ?? null;

  // Backend API calls
  const { data: history, loading: histLoading } = useFinancialHistory(apiId);
  const { data: forecast, loading: fcastLoading } = useFinancialForecast(apiId);
  const { data: apiInitiatives } = useInitiatives(apiId);
  const { data: apiDrivers } = useDrivers(apiId);

  const latestPeriod = useMemo(() => {
    if (!history || history.length === 0) return null;
    return history[history.length - 1].period;
  }, [history]);

  const { data: varianceResult } = useVariance(apiId, latestPeriod);

  // ─────────────────────────────────────────────
  // Build Monthly Financial rows from backend
  // ─────────────────────────────────────────────
  const financialRows: MonthlyFinancial[] = useMemo(() => {
    if (!history) return [];

    const monthNames = [
      "Jan","Feb","Mar","Apr","May","Jun",
      "Jul","Aug","Sep","Oct","Nov","Dec"
    ];

    return history.slice(-12).map((h, idx) => {
      const d = new Date(h.period);

      const revenue = h.revenue;
      const cogs = h.cogs;
      const gp = h.gross_profit;
      const ebitda = h.ebitda;

      const opex = gp - ebitda;
      const dep = revenue * 0.025;

      const fRow = forecast?.revenue_forecast?.[idx];

      return {
        month: monthNames[d.getMonth()],
        revenue: Math.round(revenue / 1000),
        cogs: Math.round(cogs / 1000),
        grossProfit: Math.round(gp / 1000),
        opex: Math.round(opex / 1000),
        ebitda: Math.round(ebitda / 1000),
        depreciation: Math.round(dep / 1000),
        ebit: Math.round((ebitda - dep) / 1000),
        forecast: fRow
          ? {
              revenue: Math.round(fRow.yhat / 1000),
              ebitda: 0,
            }
          : undefined,
      };
    });
  }, [history, forecast]);

  // ─────────────────────────────────────────────
  // Expense chart data from financial rows
  // ─────────────────────────────────────────────
  const expenseCategories = useMemo(() => {
    if (!financialRows.length) return [];

    const totalOpex = financialRows.reduce((s, r) => s + r.opex, 0);

    return [
      {
        category: "Operating Expenses",
        budget: Math.round(totalOpex * 1.05),
        actual: totalOpex,
        forecast: Math.round(totalOpex * 1.1),
        headcount: 0,
        avgComp: 0,
      },
    ];
  }, [financialRows]);

  // ─────────────────────────────────────────────
  // Driver dashboard data
  // ─────────────────────────────────────────────
  const driverDashData = useMemo(() => {
    if (!apiDrivers || apiDrivers.length === 0) {
      return {
        totalCustomers: 0,
        avgSalesPrice: 0,
      };
    }

    const latest = apiDrivers[apiDrivers.length - 1];

    return {
      totalCustomers: latest.customer_count || 0,
      avgSalesPrice: latest.price_per_customer || 0,
    };
  }, [apiDrivers]);

  // ─────────────────────────────────────────────
  // Initiatives from backend
  // ─────────────────────────────────────────────
  const initiativesDisplay = useMemo(() => {
    if (!apiInitiatives) return [];

    return apiInitiatives.map((ini) => ({
      name: ini.name,
      company: company.name,
      status: "In Progress",
      completion: Math.min(
        100,
        Math.round(((ini.revenue_impact || 0) / (ini.investment || 1)) * 25)
      ),
      budgeted: ini.investment || 0,
      spent: (ini.investment || 0) * 0.6,
      irr: Math.round(((ini.revenue_impact || 0) / (ini.investment || 1)) * 100),
      npv: Math.round((ini.revenue_impact || 0) * 3),
      paybackMonths: Math.round((ini.investment || 0) / (((ini.revenue_impact || 1) / 12))),
      risk:
  ((ini.investment || 0) > 5_000_000
    ? "high"
    : (ini.investment || 0) > 1_000_000
    ? "medium"
    : "low") as "high" | "medium" | "low",
    }));
  }, [apiInitiatives, company.name]);

  // ─────────────────────────────────────────────
  // Variance display
  // ─────────────────────────────────────────────
  const varianceDisplay = useMemo(() => {
  if (!varianceResult) return [];

  const variance = Math.round(varianceResult.variance / 1000);
  const variancePct = +(varianceResult.percentage * 100).toFixed(1);

  const actual = variance > 0 ? variance : 0;
  const budget = actual - variance;

  return [
    {
      item: varianceResult.agent,
      budget,
      actual,
      variance,
      variancePct,
      category: "Financial",
      explanation: varianceResult.explanation,
    },
  ];
}, [varianceResult]);

  const loading = histLoading || fcastLoading;

  return (
    <div className="p-6 space-y-6 animate-fade-up">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-foreground">
              {company.name}
            </h1>
            {loading && (
              <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />
            )}
          </div>

          <p className="text-sm text-muted-foreground mt-1">
            {company.description} · {company.sector}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Badge
            variant={
              company.status === "on-track"
                ? "default"
                : company.status === "at-risk"
                ? "secondary"
                : "destructive"
            }
          >
            {company.status}
          </Badge>

          <CompanySelector
            companies={companies}
            selected={company.id}
            onSelect={(cid) => {
              setSelectedCompany(cid);
              navigate(`/company/${cid}`);
            }}
          />
        </div>
      </div>

      <Tabs defaultValue="financials" className="space-y-4">
        <TabsList className="bg-secondary flex-wrap h-auto gap-1">
          <TabsTrigger value="financials">Financial Model</TabsTrigger>
          <TabsTrigger value="charts">Revenue & Expenses</TabsTrigger>
          <TabsTrigger value="scenarios">Scenarios</TabsTrigger>
          <TabsTrigger value="variance">Variance Analysis</TabsTrigger>
          <TabsTrigger value="drivers">Drivers</TabsTrigger>
          <TabsTrigger value="initiatives">Initiatives</TabsTrigger>
        </TabsList>

        <TabsContent value="financials">
          <FinancialModelTable data={financialRows} />
        </TabsContent>

        <TabsContent value="charts">
          <RevenueExpenseCharts
            data={financialRows}
            expenses={expenseCategories}
          />
        </TabsContent>

        <TabsContent value="scenarios">
          <ScenarioComparison />
        </TabsContent>

        <TabsContent value="variance">
          <VarianceAnalysis data={varianceDisplay} />
        </TabsContent>

        <TabsContent value="drivers">
          <DriverDashboard drivers={driverDashData} />
        </TabsContent>

        <TabsContent value="initiatives">
          <InitiativeTracker initiatives={initiativesDisplay} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
