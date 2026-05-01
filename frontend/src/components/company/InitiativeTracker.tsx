import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";

interface Initiative {
  name: string;
  company: string;
  status: string;
  completion: number;
  budgeted: number;
  spent: number;
  irr: number;
  npv: number;
  paybackMonths: number;
  risk: 'low' | 'medium' | 'high';
}

interface Props {
  initiatives: Initiative[];
}

export function InitiativeTracker({ initiatives }: Props) {
  return (
    <Card className="glass-card">
      <CardHeader>
        <CardTitle className="text-base">Strategic Initiatives</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {initiatives.map((ini, i) => (
            <div key={i} className="p-4 rounded-lg border border-border hover:border-primary/20 transition-colors">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <h4 className="text-sm font-semibold text-foreground">{ini.name}</h4>
                  <span className="text-xs text-muted-foreground">{ini.company}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={ini.risk === 'low' ? 'default' : ini.risk === 'medium' ? 'secondary' : 'destructive'} className="text-xs">
                    {ini.risk} risk
                  </Badge>
                  <Badge variant="outline" className="text-xs">{ini.status}</Badge>
                </div>
              </div>
              <div className="mb-3">
                <div className="flex justify-between text-xs text-muted-foreground mb-1">
                  <span>Completion</span>
                  <span>{ini.completion}%</span>
                </div>
                <Progress value={ini.completion} className="h-1.5" />
              </div>
              <div className="grid grid-cols-5 gap-3 text-xs">
                <div><span className="text-muted-foreground">Budget</span><div className="font-mono font-medium text-foreground">${(ini.budgeted / 1000).toFixed(1)}M</div></div>
                <div><span className="text-muted-foreground">Spent</span><div className="font-mono font-medium text-foreground">${(ini.spent / 1000).toFixed(1)}M</div></div>
                <div><span className="text-muted-foreground">IRR</span><div className="font-mono font-medium text-foreground">{ini.irr}%</div></div>
                <div><span className="text-muted-foreground">NPV</span><div className="font-mono font-medium text-foreground">${(ini.npv / 1000).toFixed(1)}M</div></div>
                <div><span className="text-muted-foreground">Payback</span><div className="font-mono font-medium text-foreground">{ini.paybackMonths}mo</div></div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
