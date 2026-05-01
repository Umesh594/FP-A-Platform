import { useEffect, useState } from "react";
import { useAppStore, KpiData } from "@/stores/appStore";
import { useKpis } from "@/hooks/useApi";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ResponsiveContainer, AreaChart, Area } from "recharts";
import { Loader2, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

function Sparkline({ data, status }: { data: number[]; status: "green" | "yellow" | "red" }) {
  const chartData = data.map((v, i) => ({ i, v }));
  const color =
    status === "green" ? "hsl(var(--success))" : status === "yellow" ? "hsl(var(--warning))" : "hsl(var(--destructive))";
  return (
    <div className="w-24 h-8">
      <ResponsiveContainer>
        <AreaChart data={chartData}>
          <defs>
            <linearGradient id={`spark-${status}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.3} />
              <stop offset="100%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <Area type="monotone" dataKey="v" stroke={color} strokeWidth={1.5} fill={`url(#spark-${status})`} dot={false} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

function StatusDot({ status }: { status: "green" | "yellow" | "red" }) {
  const cls =
    status === "green" ? "bg-success" : status === "yellow" ? "bg-warning" : "bg-destructive";
  return <span className={`inline-block w-2.5 h-2.5 rounded-full ${cls}`} />;
}

export default function KPIScorecard() {
  const { kpis: storeKpis, companies } = useAppStore();
  const [filterCompany, setFilterCompany] = useState("all");
  const [filterCategory, setFilterCategory] = useState("all");
  const [liveKpis, setLiveKpis] = useState<KpiData[]>(storeKpis);

  // Fetch live KPIs for selected company
  const selectedApiId =
    filterCompany === "all"
      ? null
      : companies.find((c) => c.id === filterCompany)?.apiId ?? null;

  const { data: apiKpis, loading, refetch } = useKpis(selectedApiId);

  useEffect(() => {
    if (!apiKpis || apiKpis.length === 0) {
      setLiveKpis(storeKpis);
      return;
    }
    const merged: KpiData[] = apiKpis.map((k) => ({
      name: k.name,
      category: "KPI",
      actual: k.actual,
      target: k.target,
      unit: "%",
      trend: [k.actual * 0.9, k.actual * 0.93, k.actual * 0.95, k.actual * 0.97, k.actual * 0.98, k.actual],
      status: k.status as "green" | "yellow" | "red",
      variance: k.target ? +((k.actual - k.target) / k.target * 100).toFixed(1) : 0,
      companyId: (
        companies.find((c) => c.apiId === (k.company_id ?? selectedApiId))?.id ??
        "cloudcrm"
      ) as KpiData["companyId"],
    }));
    setLiveKpis(merged);
  }, [apiKpis, storeKpis, filterCompany, selectedApiId, companies]);

  const filtered = liveKpis.filter((k) => {
    if (filterCompany !== "all" && k.companyId !== filterCompany) return false;
    if (filterCategory !== "all" && k.category !== filterCategory) return false;
    return true;
  });

  const categories = [...new Set(liveKpis.map((k) => k.category))];
  const greenCount = filtered.filter((k) => k.status === "green").length;
  const yellowCount = filtered.filter((k) => k.status === "yellow").length;
  const redCount = filtered.filter((k) => k.status === "red").length;

  return (
    <div className="p-6 space-y-6 animate-fade-up">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground">KPI Scorecard</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Monitor key performance indicators across all portfolio companies
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Select value={filterCompany} onValueChange={setFilterCompany}>
            <SelectTrigger className="w-44 bg-secondary"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Companies</SelectItem>
              {companies.map((c) => <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>)}
            </SelectContent>
          </Select>
          <Select value={filterCategory} onValueChange={setFilterCategory}>
            <SelectTrigger className="w-36 bg-secondary"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Categories</SelectItem>
              {categories.map((c) => <SelectItem key={c} value={c}>{c}</SelectItem>)}
            </SelectContent>
          </Select>
          <Button variant="outline" size="sm" onClick={refetch} disabled={loading}>
            {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
          </Button>
        </div>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: "On Track", count: greenCount, color: "bg-success/10", dot: "bg-success" },
          { label: "At Risk", count: yellowCount, color: "bg-warning/10", dot: "bg-warning" },
          { label: "Off Track", count: redCount, color: "bg-destructive/10", dot: "bg-destructive" },
        ].map((item) => (
          <Card key={item.label} className="glass-card">
            <CardContent className="pt-4 flex items-center gap-3">
              <div className={`w-10 h-10 rounded-lg ${item.color} flex items-center justify-center`}>
                <span className={`w-3 h-3 rounded-full ${item.dot}`} />
              </div>
              <div>
                <div className="text-2xl font-bold text-foreground">{item.count}</div>
                <div className="text-xs text-muted-foreground">{item.label}</div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* KPI Table */}
      <Card className="glass-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border">
                {["Status", "KPI", "Category", "Actual", "Target", "Variance", "Trend (12M)", "Company"].map((h) => (
                  <th key={h} className={`text-xs font-medium text-muted-foreground p-4 ${h === "Actual" || h === "Target" || h === "Variance" ? "text-right" : h === "Trend (12M)" ? "text-center" : "text-left"}`}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map((kpi, idx) => {
                const comp = companies.find((c) => c.id === kpi.companyId);
                const isNegativeGood = kpi.name.includes("Churn") || kpi.name.includes("Cost") || kpi.name.includes("CAC");
                const favorable = isNegativeGood ? kpi.variance <= 0 : kpi.variance >= 0;
                return (
                  <tr key={idx} className="border-b border-border/50 hover:bg-secondary/50 transition-colors">
                    <td className="p-4"><StatusDot status={kpi.status} /></td>
                    <td className="p-4 text-sm font-medium text-foreground">{kpi.name}</td>
                    <td className="p-4"><Badge variant="secondary" className="text-xs">{kpi.category}</Badge></td>
                    <td className="p-4 text-right font-mono text-sm text-foreground">
                      {kpi.unit === "$" || kpi.unit === "$M" || kpi.unit === "$K" ? "$" : ""}
                      {kpi.actual.toLocaleString()}
                      {kpi.unit === "%" ? "%" : kpi.unit === "x" ? "x" : kpi.unit === "$M" ? "M" : kpi.unit === "$K" ? "K" : kpi.unit === "M" ? "M" : ""}
                    </td>
                    <td className="p-4 text-right font-mono text-sm text-muted-foreground">
                      {kpi.unit === "$" || kpi.unit === "$M" || kpi.unit === "$K" ? "$" : ""}
                      {kpi.target.toLocaleString()}
                      {kpi.unit === "%" ? "%" : kpi.unit === "x" ? "x" : kpi.unit === "$M" ? "M" : kpi.unit === "$K" ? "K" : kpi.unit === "M" ? "M" : ""}
                    </td>
                    <td className={`p-4 text-right font-mono text-sm font-medium ${favorable ? "text-success" : "text-destructive"}`}>
                      {kpi.variance > 0 ? "+" : ""}{kpi.variance.toFixed(1)}%
                    </td>
                    <td className="p-4 flex justify-center">
                      <Sparkline data={kpi.trend} status={kpi.status} />
                    </td>
                    <td className="p-4 text-sm text-muted-foreground">{comp?.name ?? kpi.companyId}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
