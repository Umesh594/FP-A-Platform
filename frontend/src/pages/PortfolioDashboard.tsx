import { useEffect } from "react";
import { useAppStore } from "@/stores/appStore";
import { useCompanies } from "@/hooks/useApi";
import { MetricCard } from "@/components/dashboard/MetricCard";
import { CompanyGrid } from "@/components/dashboard/CompanyGrid";
import { AgentActivityFeed } from "@/components/dashboard/AgentActivityFeed";
import { PlanningTimeline } from "@/components/dashboard/PlanningTimeline";
import { PortfolioCharts } from "@/components/dashboard/PortfolioCharts";
import { TrendingUp, DollarSign, BarChart3, Building2, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { ApiCompany } from "@/api/client";
import type { CompanyId, PortfolioCompany } from "@/stores/appStore";

const companySlugByApiId: Record<number, CompanyId> = {
  1: "cloudcrm",
  2: "manufacturetech",
  3: "healthcaretech",
  4: "ecommerce",
  5: "fintech",
  6: "industrial",
};

function getCompanyStatus(ebitdaMargin: number): PortfolioCompany["status"] {
  if (ebitdaMargin >= 15) return "on-track";
  if (ebitdaMargin >= 10) return "at-risk";
  return "off-track";
}

function mapCompanyFromApi(company: ApiCompany): PortfolioCompany {
  const revenue = company.revenue || 0;
  const ebitda = company.ebitda || 0;
  const ebitdaMargin = revenue ? (ebitda / revenue) * 100 : 0;
  const arr = company.arr || 0;

  return {
    id: companySlugByApiId[company.id] || "cloudcrm",
    apiId: company.id,
    name: company.name,
    sector: company.sector || "Portfolio Company",
    arr: +(arr / 1_000_000).toFixed(1),
    revenue: +(revenue / 1_000_000).toFixed(1),
    ebitda: +(ebitda / 1_000_000).toFixed(1),
    ebitdaMargin: +ebitdaMargin.toFixed(1),
    budgetVariance: 0,
    forecastVariance: 0,
    status: getCompanyStatus(ebitdaMargin),
    growthRate: 0,
    employees: company.employees || 0,
    description: `${company.sector || "Portfolio"} company from seeded portfolio dataset`,
  };
}

export default function PortfolioDashboard() {
  const { companies, agentActivities, setCompanies } = useAppStore();
  const { data: apiCompanies, loading, refetch } = useCompanies();

  useEffect(() => {
  if (!apiCompanies) return;
  setCompanies(apiCompanies.map(mapCompanyFromApi));
}, [apiCompanies, setCompanies]);

  const totalRevenue = companies.reduce((s, c) => s + c.revenue, 0);
  const totalEbitda = companies.reduce((s, c) => s + c.ebitda, 0);
  const avgMargin = totalRevenue ? (totalEbitda / totalRevenue) * 100 : 0;

  if (loading && companies.length === 0) {
    return (
      <div className="p-6 text-sm text-muted-foreground">
        Loading seeded portfolio data...
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 animate-fade-up">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">
            Portfolio Dashboard
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Summit Growth Partners — 6 Portfolio Companies
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-xs text-muted-foreground bg-secondary px-3 py-1.5 rounded-lg">
            <div className="status-dot-green" />
            {loading ? "Refreshing…" : "Live data"}
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={refetch}
            disabled={loading}
          >
            <RefreshCw
              className={`w-3.5 h-3.5 mr-1.5 ${loading ? "animate-spin" : ""}`}
            />
            Refresh
          </Button>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total Revenue"
          value={`$${totalRevenue.toFixed(1)}M`}
          icon={DollarSign}
          subtitle="Seeded portfolio data"
        />

        <MetricCard
          title="Total EBITDA"
          value={`$${totalEbitda.toFixed(1)}M`}
          icon={TrendingUp}
          subtitle="Seeded portfolio data"
        />

        <MetricCard
          title="Avg EBITDA Margin"
          value={`${avgMargin.toFixed(1)}%`}
          icon={BarChart3}
          subtitle="Calculated from seed data"
        />

        <MetricCard
          title="Portfolio Companies"
          value={`${companies.length}`}
          icon={Building2}
          subtitle="Loaded from backend seed"
        />
      </div>

      <PortfolioCharts companies={companies} />

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2">
          <CompanyGrid companies={companies} />
        </div>

        <div>
          <AgentActivityFeed activities={agentActivities} />
        </div>
      </div>

      {/* Timeline (dummy removed) */}
      <PlanningTimeline milestones={[]} />
    </div>
  );
}
