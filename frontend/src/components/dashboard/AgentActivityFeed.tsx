import { AgentActivity } from "@/stores/appStore";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Bot, CheckCircle, AlertTriangle, Loader2, XCircle } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

interface Props {
  activities: AgentActivity[];
}

const statusIcons = {
  running: <Loader2 className="w-3.5 h-3.5 text-info animate-spin" />,
  completed: <CheckCircle className="w-3.5 h-3.5 text-success" />,
  alert: <AlertTriangle className="w-3.5 h-3.5 text-warning" />,
  error: <XCircle className="w-3.5 h-3.5 text-destructive" />,
};

export function AgentActivityFeed({ activities }: Props) {
  return (
    <Card className="glass-card h-full">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            <Bot className="w-4 h-4 text-primary" />
            Agent Activity
          </CardTitle>
          <Badge variant="secondary" className="text-xs">Live</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-1 max-h-96 overflow-y-auto">
        {activities.map((a) => (
          <div key={a.id} className="flex gap-3 p-2 rounded-lg hover:bg-secondary/50 transition-colors animate-slide-in">
            <div className="mt-0.5 shrink-0">{statusIcons[a.status]}</div>
            <div className="min-w-0">
              <div className="text-xs text-foreground leading-relaxed">
                <span className="font-medium text-primary">{a.agentName}</span>
                {' '}{a.action}
              </div>
              {a.detail && <div className="text-[10px] text-muted-foreground mt-0.5">{a.detail}</div>}
              <div className="text-[10px] text-muted-foreground/60 mt-0.5">
                {formatDistanceToNow(a.timestamp, { addSuffix: true })}
              </div>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
