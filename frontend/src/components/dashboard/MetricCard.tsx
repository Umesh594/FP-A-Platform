import { Card, CardContent } from "@/components/ui/card";
import { LucideIcon, TrendingUp, TrendingDown } from "lucide-react";

interface MetricCardProps {
  title: string;
  value: string;
  change?: number;
  icon: LucideIcon;
  subtitle: string;
}

export function MetricCard({ title, value, change, icon: Icon, subtitle }: MetricCardProps) {
  const positive = change >= 0;
  return (
    <Card className="glass-card hover:metric-glow transition-all">
      <CardContent className="pt-5">
        <div className="flex items-start justify-between">
          <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
            <Icon className="w-5 h-5 text-primary" />
          </div>
          {change !== undefined && (
            <div className={`flex items-center gap-1 text-xs font-medium ${positive ? 'text-success' : 'text-destructive'}`}>
              {positive ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
              {positive ? '+' : ''}{change.toFixed(1)}%
            </div>
          )}
        </div>
        <div className="mt-3">
          <div className="text-2xl font-bold text-foreground tracking-tight">{value}</div>
          <div className="text-xs text-muted-foreground mt-0.5">{title}</div>
          <div className="text-[10px] text-muted-foreground/60 mt-0.5">{subtitle}</div>
        </div>
      </CardContent>
    </Card>
  );
}
