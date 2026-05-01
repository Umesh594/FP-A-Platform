import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface Milestone {
  name: string;
  phase: number;
  start: string;
  end: string;
  status: 'completed' | 'in-progress' | 'upcoming';
}

interface Props {
  milestones: Milestone[];
}

export function PlanningTimeline({ milestones }: Props) {
  return (
    <Card className="glass-card">
      <CardHeader>
        <CardTitle className="text-base">Planning Timeline — FY2026</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="relative">
          <div className="absolute left-4 top-0 bottom-0 w-px bg-border" />
          <div className="space-y-4">
            {milestones.map((m, i) => (
              <div key={i} className="flex gap-4 ml-1">
                <div className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 z-10 text-xs font-bold ${
                  m.status === 'completed' ? 'bg-success text-success-foreground' :
                  m.status === 'in-progress' ? 'gradient-primary text-primary-foreground animate-pulse-glow' :
                  'bg-secondary text-secondary-foreground'
                }`}>
                  {m.phase}
                </div>
                <div className="flex-1 pb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-foreground">{m.name}</span>
                    <Badge variant={
                      m.status === 'completed' ? 'default' :
                      m.status === 'in-progress' ? 'secondary' : 'outline'
                    } className="text-xs">
                      {m.status}
                    </Badge>
                  </div>
                  <div className="text-xs text-muted-foreground mt-0.5">
                    {m.start} → {m.end}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
