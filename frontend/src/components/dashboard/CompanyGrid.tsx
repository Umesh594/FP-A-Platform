import { PortfolioCompany } from "@/stores/appStore";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, Users } from "lucide-react";
import { useNavigate } from "react-router-dom";

interface CompanyGridProps {
  companies: PortfolioCompany[];
}

export function CompanyGrid({ companies }: CompanyGridProps) {
  const navigate = useNavigate();

  return (
    <Card className="glass-card">
      <CardHeader>
        <CardTitle className="text-base">Portfolio Companies</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {companies.map((c) => (
            <div
              key={c.id}
              onClick={() => navigate(`/company/${c.id}`)}
              className="p-4 rounded-lg border border-border hover:border-primary/30 hover:metric-glow transition-all cursor-pointer"
            >
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-semibold text-foreground truncate">{c.name}</h3>
                <Badge
                  variant={c.status === 'on-track' ? 'default' : c.status === 'at-risk' ? 'secondary' : 'destructive'}
                  className="text-xs shrink-0"
                >
                  {c.status}
                </Badge>
              </div>
              <p className="text-xs text-muted-foreground mb-3">{c.sector}</p>
              <div className="grid grid-cols-3 gap-2 text-xs">
                <div>
                  <div className="text-muted-foreground">Revenue</div>
                  <div className="font-mono font-semibold text-foreground">${c.revenue}M</div>
                </div>
                <div>
                  <div className="text-muted-foreground">EBITDA</div>
                  <div className="font-mono font-semibold text-foreground">${c.ebitda}M</div>
                </div>
                <div>
                  <div className="text-muted-foreground">Margin</div>
                  <div className="font-mono font-semibold text-foreground">{c.ebitdaMargin}%</div>
                </div>
              </div>
              <div className="flex items-center justify-between mt-3 pt-2 border-t border-border">
                <div className="flex items-center gap-1 text-xs text-muted-foreground">
                  <Users className="w-3 h-3" />{c.employees}
                </div>
                <div className={`flex items-center gap-1 text-xs font-medium ${c.growthRate >= 0 ? 'text-success' : 'text-destructive'}`}>
                  <TrendingUp className="w-3 h-3" />{c.growthRate}% YoY
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
