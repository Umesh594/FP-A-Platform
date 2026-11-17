import { useEffect, useMemo, useState } from "react";
import { RefreshCw, UsersRound } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { getApiBaseUrl } from "@/lib/api";

type WorkforceRow = {
  company_id: number;
  department: string;
  period: string;
  actual_headcount: number;
  planned_headcount: number;
  headcount_variance: number;
  actual_monthly_cost: number;
  planned_monthly_cost: number;
  cost_variance: number;
  open_requisitions: number;
  data_quality_status: string;
};

const currency = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });

export default function WorkforcePlanning() {
  const [rows, setRows] = useState<WorkforceRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`${getApiBaseUrl()}/workforce/analytics/dataset`);
      if (!response.ok) throw new Error(`Workforce analytics request failed (${response.status})`);
      setRows(await response.json());
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to load workforce planning data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { void load(); }, []);

  const summary = useMemo(() => rows.reduce((acc, row) => ({
    actual: acc.actual + row.actual_headcount,
    planned: acc.planned + row.planned_headcount,
    requisitions: acc.requisitions + row.open_requisitions,
    costVariance: acc.costVariance + row.cost_variance,
  }), { actual: 0, planned: 0, requisitions: 0, costVariance: 0 }), [rows]);

  return (
    <div className="p-6 space-y-6 animate-fade-up">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Workforce Planning</h1>
          <p className="text-sm text-muted-foreground mt-1">Department-level headcount, hiring pipeline, and planned-versus-actual cost.</p>
        </div>
        <Button variant="outline" size="sm" onClick={() => void load()} disabled={loading}>
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
        </Button>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: "Actual Headcount", value: summary.actual },
          { label: "Approved Plan", value: summary.planned },
          { label: "Open Requisitions", value: summary.requisitions },
          { label: "Monthly Cost Variance", value: currency.format(summary.costVariance) },
        ].map((metric) => (
          <Card key={metric.label} className="glass-card">
            <CardContent className="pt-4 flex items-center gap-3">
              <UsersRound className="w-4 h-4 text-primary" />
              <div><p className="text-lg font-semibold">{metric.value}</p><p className="text-xs text-muted-foreground">{metric.label}</p></div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card className="glass-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead><tr className="border-b border-border text-left text-xs text-muted-foreground">
              {['Department', 'Month', 'Actual', 'Plan', 'Variance', 'Cost variance', 'Open roles', 'Quality'].map((heading) => <th className="p-4 font-medium" key={heading}>{heading}</th>)}
            </tr></thead>
            <tbody>
              {rows.map((row) => <tr className="border-b border-border/50" key={`${row.department}-${row.period}`}>
                <td className="p-4 font-medium">{row.department}</td><td className="p-4">{row.period}</td><td className="p-4">{row.actual_headcount}</td><td className="p-4">{row.planned_headcount}</td>
                <td className={`p-4 ${row.headcount_variance > 0 ? "text-warning" : "text-success"}`}>{row.headcount_variance > 0 ? "+" : ""}{row.headcount_variance}</td>
                <td className={`p-4 ${row.cost_variance > 0 ? "text-warning" : "text-success"}`}>{currency.format(row.cost_variance)}</td><td className="p-4">{row.open_requisitions}</td>
                <td className="p-4"><Badge variant="secondary">{row.data_quality_status}</Badge></td>
              </tr>)}
              {!loading && rows.length === 0 && <tr><td className="p-6 text-muted-foreground" colSpan={8}>No workforce data has been synced yet.</td></tr>}
            </tbody>
          </table>
        </div>
      </Card>
      {error && <p className="text-sm text-destructive">{error}</p>}
    </div>
  );
}
