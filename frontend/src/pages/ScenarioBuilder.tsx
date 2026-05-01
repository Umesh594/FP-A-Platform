import { useEffect } from "react";
import { useAppStore, ScenarioAssumptions } from "@/stores/appStore";
import { useScenarios } from "@/hooks/useApi";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
import { Loader2 } from "lucide-react";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
} from "recharts";

const assumptionLabels: Record<keyof ScenarioAssumptions, { label: string; unit: string; min: number; max: number }> = {
  revenueGrowth: { label: "Revenue Growth", unit: "%", min: -10, max: 50 },
  grossMargin: { label: "Gross Margin", unit: "%", min: 40, max: 90 },
  headcountGrowth: { label: "Headcount Growth", unit: "%", min: -10, max: 30 },
  churnRate: { label: "Churn Rate", unit: "%", min: 0, max: 15 },
  priceIncrease: { label: "Price Increase", unit: "%", min: -5, max: 20 },
  opexGrowth: { label: "OpEx Growth", unit: "%", min: -5, max: 25 },
};

function computePL(a: ScenarioAssumptions) {
  const base = 35200;
  const revenue = base * (1 + a.revenueGrowth / 100);
  const cogs = revenue * (1 - a.grossMargin / 100);
  const gp = revenue - cogs;
  const opex = 19200 * (1 + a.opexGrowth / 100);
  const ebitda = gp - opex;
  return {
    revenue: +(revenue / 1000).toFixed(1),
    grossProfit: +(gp / 1000).toFixed(1),
    opex: +(opex / 1000).toFixed(1),
    ebitda: +(ebitda / 1000).toFixed(1),
    margin: +((ebitda / revenue) * 100).toFixed(1),
  };
}

export default function ScenarioBuilder() {
  const { scenarioAssumptions, updateAssumption, companies } = useAppStore();
  if (!scenarioAssumptions) return null;

  // Fetch live Monte Carlo scenarios using CloudCRM as base
  const baseRevenue = companies?.[0]?.revenue
  ? companies[0].revenue * 1_000_000
  : 0;
  const baseExpense = companies?.[0]
  ? companies[0].revenue * (1 - companies[0].ebitdaMargin / 100) * 1_000_000
  : 0;
  const { data: liveScenarios, loading } = useScenarios(baseRevenue, baseExpense);

  const scenarios = (Object.entries(scenarioAssumptions) as [
  "base" | "upside" | "downside",
  ScenarioAssumptions
][]).map(([name, a]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    key: name,
    assumptions: a,
    ...computePL(a),
  }));
  const scenariosMap = {
  base: computePL(scenarioAssumptions.base),
  upside: computePL(scenarioAssumptions.upside),
  downside: computePL(scenarioAssumptions.downside),
};
  // Build comparison data — prefer live backend values when available
  const comparisonData = [
    {
      metric: "Revenue ($M)",
      Base: liveScenarios?.scenarios?.base?.revenue?.mean
  ? +(liveScenarios.scenarios.base.revenue.mean / 1_000_000).toFixed(1)
  : scenariosMap.base.revenue,

Upside: liveScenarios?.scenarios?.optimistic?.revenue?.mean
  ? +(liveScenarios.scenarios.optimistic.revenue.mean / 1_000_000).toFixed(1)
  : scenariosMap.upside.revenue,

Downside: liveScenarios?.scenarios?.pessimistic?.revenue?.mean
  ? +(liveScenarios.scenarios.pessimistic.revenue.mean / 1_000_000).toFixed(1)
  : scenariosMap.downside.revenue,
    },
    {
  metric: "EBITDA ($M)",
  Base: scenariosMap.base.ebitda,
  Upside: scenariosMap.upside.ebitda,
  Downside: scenariosMap.downside.ebitda,
},
{
  metric: "Gross Profit ($M)",
  Base: scenariosMap.base.grossProfit,
  Upside: scenariosMap.upside.grossProfit,
  Downside: scenariosMap.downside.grossProfit,
},
  ];
  const baseScenario = scenarioAssumptions?.base;
  if (!baseScenario) return null;

  const tornadoData = (Object.entries(assumptionLabels) as [keyof ScenarioAssumptions, typeof assumptionLabels[keyof ScenarioAssumptions]][])
  .map(([key, meta]) => {
    const base = computePL(baseScenario);

    const high = computePL({
      ...baseScenario,
      [key]: meta.max * 0.7
    });

    const low = computePL({
      ...baseScenario,
      [key]: meta.min + (meta.max - meta.min) * 0.3
    });

    return {
      driver: meta.label,
      upside: +(high.ebitda - base.ebitda).toFixed(1),
      downside: +(low.ebitda - base.ebitda).toFixed(1),
    };
  })
  .sort((a, b) => Math.abs(b.upside - b.downside) - Math.abs(a.upside - a.downside));

  const radarData = (Object.entries(assumptionLabels) as [keyof ScenarioAssumptions, typeof assumptionLabels[keyof ScenarioAssumptions]][])
  .map(([key]) => ({
    metric: assumptionLabels[key].label,
    Base: scenarioAssumptions?.base?.[key] ?? 0,
    Upside: scenarioAssumptions?.upside?.[key] ?? 0,
    Downside: scenarioAssumptions?.downside?.[key] ?? 0,
  }));

  return (
    <div className="p-6 space-y-6 animate-fade-up">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Scenario Builder</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Model base, upside, and downside scenarios with real-time P&L impact
          </p>
        </div>
        {loading && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
            Loading Monte Carlo…
          </div>
        )}
      </div>

      {/* Monte Carlo confidence from backend */}
      {liveScenarios?.scenarios?.base && (
        <div className="grid grid-cols-3 gap-4">
          {[
  { label: "Base Case Revenue", val: liveScenarios?.scenarios?.base?.revenue },
  { label: "Optimistic Revenue", val: liveScenarios?.scenarios?.optimistic?.revenue },
  { label: "Pessimistic Revenue", val: liveScenarios?.scenarios?.pessimistic?.revenue },
]
.filter(v => v.val)
.map(({ label, val }) => (
            <Card key={label} className="glass-card">
              <CardContent className="pt-4">
                <div className="text-xs text-muted-foreground mb-1">{label} (Monte Carlo)</div>
                <div className="text-lg font-bold font-mono text-foreground">
                  ${(val.mean / 1_000_000).toFixed(1)}M
                </div>
                <div className="text-xs text-muted-foreground mt-1">
                  Range: ${(val.min / 1_000_000).toFixed(1)}M – ${(val.max / 1_000_000).toFixed(1)}M
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Assumption sliders */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {scenarios.map((s) => (
          <Card key={s.key} className="glass-card">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">{s.name} Case</CardTitle>
                <Badge variant={s.key === "upside" ? "default" : s.key === "downside" ? "destructive" : "secondary"}>
                  {s.margin}% margin
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {(Object.keys(assumptionLabels) as (keyof ScenarioAssumptions)[]).map((key) => {
                const meta = assumptionLabels[key];
                return (
                  <div key={key} className="space-y-1.5">
                    <div className="flex justify-between text-xs">
                      <span className="text-muted-foreground">{meta.label}</span>
                      <span className="font-mono font-medium text-foreground">{s.assumptions[key]}{meta.unit}</span>
                    </div>
                    <Slider value={[s.assumptions[key]]} onValueChange={([v]) =>
  updateAssumption(s.key as "base" | "upside" | "downside", key, v)
} min={meta.min} max={meta.max} step={0.5} className="w-full" />
                  </div>
                );
              })}
              <div className="pt-3 border-t border-border space-y-1.5">
                <div className="flex justify-between text-xs"><span className="text-muted-foreground">Revenue</span><span className="font-mono font-semibold">${s.revenue}M</span></div>
                <div className="flex justify-between text-xs"><span className="text-muted-foreground">EBITDA</span><span className="font-mono font-semibold">${s.ebitda}M</span></div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="glass-card">
          <CardHeader><CardTitle className="text-base">Scenario Comparison</CardTitle></CardHeader>
          <CardContent>
            <div className="h-80">
              <ResponsiveContainer>
                <BarChart data={comparisonData} barGap={4}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="metric" tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} />
                  <YAxis tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} />
                  <Tooltip contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 8, fontSize: 12 }} />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  <Bar dataKey="Base" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="Upside" fill="hsl(var(--success))" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="Downside" fill="hsl(var(--destructive))" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card className="glass-card">
          <CardHeader><CardTitle className="text-base">Sensitivity Analysis (Tornado)</CardTitle></CardHeader>
          <CardContent>
            <div className="h-80">
              <ResponsiveContainer>
                <BarChart data={tornadoData} layout="vertical" barGap={0}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis type="number" tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} />
                  <YAxis dataKey="driver" type="category" width={120} tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} />
                  <Tooltip contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 8, fontSize: 12 }} />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  <Bar dataKey="upside" fill="hsl(var(--success))" radius={[0, 4, 4, 0]} name="Upside Impact ($M)" />
                  <Bar dataKey="downside" fill="hsl(var(--destructive))" radius={[4, 0, 0, 4]} name="Downside Impact ($M)" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card className="glass-card lg:col-span-2">
          <CardHeader><CardTitle className="text-base">Scenario Radar — Assumption Profiles</CardTitle></CardHeader>
          <CardContent>
            <div className="h-80">
              <ResponsiveContainer>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="hsl(var(--border))" />
                  <PolarAngleAxis dataKey="metric" tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} />
                  <PolarRadiusAxis tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} />
                  <Radar name="Base" dataKey="Base" stroke="hsl(var(--primary))" fill="hsl(var(--primary))" fillOpacity={0.15} />
                  <Radar name="Upside" dataKey="Upside" stroke="hsl(var(--success))" fill="hsl(var(--success))" fillOpacity={0.1} />
                  <Radar name="Downside" dataKey="Downside" stroke="hsl(var(--destructive))" fill="hsl(var(--destructive))" fillOpacity={0.1} />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}