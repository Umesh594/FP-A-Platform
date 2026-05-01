import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface VarianceItem {
  item: string;
  budget: number;
  actual: number;
  variance: number;
  variancePct: number;
  category: string;
  explanation: string;
}

interface Props {
  data: VarianceItem[];
}

export function VarianceAnalysis({ data }: Props) {
  return (
    <Card className="glass-card">
      <CardHeader>
        <CardTitle className="text-base">Variance Analysis — Budget vs Actual ($K)</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {data.map((v, i) => {
            const favorable = v.variance >= 0;
            return (
              <div key={i} className="p-4 rounded-lg border border-border hover:border-primary/20 transition-colors">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <h4 className="text-sm font-semibold text-foreground">{v.item}</h4>
                    <Badge variant="outline" className="text-xs">{v.category}</Badge>
                  </div>
                  <div className={`text-sm font-mono font-bold ${favorable ? 'text-success' : 'text-destructive'}`}>
                    {favorable ? '+' : ''}{v.variancePct.toFixed(1)}%
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-4 mb-3 text-xs">
                  <div><span className="text-muted-foreground">Budget</span><div className="font-mono font-medium text-foreground">${v.budget.toLocaleString()}</div></div>
                  <div><span className="text-muted-foreground">Actual</span><div className="font-mono font-medium text-foreground">${v.actual.toLocaleString()}</div></div>
                  <div><span className="text-muted-foreground">Variance</span><div className={`font-mono font-medium ${favorable ? 'text-success' : 'text-destructive'}`}>${Math.abs(v.variance).toLocaleString()}</div></div>
                </div>
                <div className="text-xs text-muted-foreground bg-secondary/50 rounded p-2.5 leading-relaxed">
                  💡 {v.explanation}
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
