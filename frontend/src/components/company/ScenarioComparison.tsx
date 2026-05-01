import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from "recharts";

export function ScenarioComparison() {
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const scenarioData = months.map((m, i) => ({
    month: m,
    Base: 2650 + i * 80,
    Upside: 2800 + i * 120,
    Downside: 2400 + i * 40,
  }));

  const summary = [
    { scenario: 'Base', revenue: '$40.5M', ebitda: '$8.1M', margin: '20.0%', probability: '55%' },
    { scenario: 'Upside', revenue: '$48.2M', ebitda: '$12.5M', margin: '25.9%', probability: '25%' },
    { scenario: 'Downside', revenue: '$32.4M', ebitda: '$3.2M', margin: '9.9%', probability: '20%' },
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-3 gap-4">
        {summary.map((s) => (
          <Card key={s.scenario} className="glass-card">
            <CardContent className="pt-5">
              <div className="flex items-center justify-between mb-3">
                <Badge variant={s.scenario === 'Upside' ? 'default' : s.scenario === 'Downside' ? 'destructive' : 'secondary'}>
                  {s.scenario}
                </Badge>
                <span className="text-xs text-muted-foreground">{s.probability} prob.</span>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between text-xs"><span className="text-muted-foreground">Revenue</span><span className="font-mono font-semibold text-foreground">{s.revenue}</span></div>
                <div className="flex justify-between text-xs"><span className="text-muted-foreground">EBITDA</span><span className="font-mono font-semibold text-foreground">{s.ebitda}</span></div>
                <div className="flex justify-between text-xs"><span className="text-muted-foreground">Margin</span><span className="font-mono font-semibold text-foreground">{s.margin}</span></div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card className="glass-card">
        <CardHeader><CardTitle className="text-base">Monthly Revenue by Scenario ($K)</CardTitle></CardHeader>
        <CardContent>
          <div className="h-72">
            <ResponsiveContainer>
              <BarChart data={scenarioData} barGap={2}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="month" tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} />
                <YAxis tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} />
                <Tooltip contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 8, fontSize: 12 }} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Bar dataKey="Base" fill="hsl(var(--primary))" radius={[3, 3, 0, 0]} />
                <Bar dataKey="Upside" fill="hsl(var(--success))" radius={[3, 3, 0, 0]} />
                <Bar dataKey="Downside" fill="hsl(var(--destructive))" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
