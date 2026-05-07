import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  BrainCircuit,
  CheckCircle2,
  Database,
  GitBranch,
  Play,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  Timer,
  Wrench,
} from "lucide-react";
import { api, type AgentRunDetail, type AgentRunSummary, type DataSource, type Recommendation } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

function MetricTile({ label, value, icon: Icon }: { label: string; value: string; icon: typeof Activity }) {
  return (
    <Card>
      <CardContent className="p-4 flex items-center justify-between">
        <div>
          <p className="text-xs text-muted-foreground">{label}</p>
          <p className="text-xl font-semibold mt-1">{value}</p>
        </div>
        <Icon className="w-5 h-5 text-primary" />
      </CardContent>
    </Card>
  );
}

export default function AgentIntelligence() {
  const [runs, setRuns] = useState<AgentRunSummary[]>([]);
  const [selectedRun, setSelectedRun] = useState<AgentRunDetail | null>(null);
  const [metrics, setMetrics] = useState<Record<string, number>>({});
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [sources, setSources] = useState<DataSource[]>([]);
  const [loading, setLoading] = useState(false);
  const [companyId, setCompanyId] = useState(1);
  const [toolResult, setToolResult] = useState<Record<string, unknown> | null>(null);

  const latestRunId = runs[0]?.run_id;

  async function refresh(nextRunId?: string) {
    const [runRows, summary, recRows, sourceRows] = await Promise.all([
      api.getAgentRuns(),
      api.getObservabilitySummary(),
      api.getRecommendations(),
      api.getDataSources(),
    ]);
    setRuns(runRows);
    setMetrics(summary);
    setRecommendations(recRows);
    setSources(sourceRows);
    const detailId = nextRunId || selectedRun?.run.run_id || runRows[0]?.run_id;
    if (detailId) {
      setSelectedRun(await api.getAgentRun(detailId));
    }
  }

  useEffect(() => {
    refresh().catch(() => undefined);
  }, []);

  async function runCycle() {
    setLoading(true);
    try {
      const result = await api.runAgentCycle(companyId);
      await refresh(result.run_id);
    } finally {
      setLoading(false);
    }
  }

  async function syncPipeline(sourceId?: number) {
    setLoading(true);
    try {
      await api.runPipeline(sourceId);
      await refresh();
    } finally {
      setLoading(false);
    }
  }

  async function runBeam(sourceId?: number) {
    setLoading(true);
    try {
      setToolResult(await api.runBeamPipeline(sourceId));
      await refresh();
    } finally {
      setLoading(false);
    }
  }

  async function runSpark(sourceId?: number) {
    setLoading(true);
    try {
      setToolResult(await api.runSparkPipeline(sourceId));
      await refresh();
    } finally {
      setLoading(false);
    }
  }

  async function testSource(sourceId: number) {
    setToolResult(await api.testDataSource(sourceId));
  }

  async function syncSource(sourceId: number) {
    setLoading(true);
    try {
      setToolResult(await api.syncDataSource(sourceId));
      await refresh();
    } finally {
      setLoading(false);
    }
  }

  async function showMcp() {
    setToolResult(await api.getMcpServer());
  }

  async function rerunEvals() {
    if (!selectedRun) return;
    await api.runEvals(selectedRun.run.run_id);
    await refresh(selectedRun.run.run_id);
  }

  async function runTool(toolName: string) {
    setToolResult(await api.executeSecureTool(toolName, companyId));
  }

  const evalPassRate = useMemo(() => {
    if (!selectedRun?.evals.length) return "0%";
    const passed = selectedRun.evals.filter((e) => e.passed).length;
    return `${Math.round((passed / selectedRun.evals.length) * 100)}%`;
  }, [selectedRun]);

  return (
    <div className="p-6 space-y-6 animate-fade-up">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Agent Intelligence</h1>
          <p className="text-sm text-muted-foreground mt-1">
            LangGraph-style orchestration, ReAct traces, evals, recommendations, connectors, and secure MCP-style tools.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <select
            value={companyId}
            onChange={(event) => setCompanyId(Number(event.target.value))}
            className="h-9 rounded-md border bg-background px-3 text-sm"
          >
            {[1, 2, 3, 4, 5, 6].map((id) => (
              <option key={id} value={id}>
                Company {id}
              </option>
            ))}
          </select>
          <Button onClick={runCycle} disabled={loading}>
            {loading ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <Play className="w-4 h-4 mr-2" />}
            Run Cycle
          </Button>
          <Button variant="outline" onClick={() => refresh()} disabled={loading}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
          <Button variant="outline" onClick={showMcp}>
            <ShieldCheck className="w-4 h-4 mr-2" />
            MCP
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <MetricTile label="Agent Runs" value={`${metrics.agent_runs || 0}`} icon={BrainCircuit} />
        <MetricTile label="P95 Latency" value={`${Math.round(metrics.p95_latency_ms || 0)}ms`} icon={Timer} />
        <MetricTile label="Tokens/sec" value={`${metrics.tokens_sec || 0}`} icon={Sparkles} />
        <MetricTile label="Eval Pass Rate" value={evalPassRate} icon={CheckCircle2} />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <Card className="xl:col-span-1">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <GitBranch className="w-4 h-4" />
              Agent Runs
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {runs.length === 0 && <p className="text-sm text-muted-foreground">No runs yet. Start a planning cycle.</p>}
            {runs.map((run) => (
              <button
                key={run.run_id}
                onClick={async () => setSelectedRun(await api.getAgentRun(run.run_id))}
                className={`w-full text-left rounded-md border p-3 hover:bg-muted transition-colors ${
                  selectedRun?.run.run_id === run.run_id || (!selectedRun && run.run_id === latestRunId) ? "border-primary" : ""
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm font-medium truncate">{run.run_id}</span>
                  <Badge>{run.status}</Badge>
                </div>
                <p className="text-xs text-muted-foreground mt-1">Company {run.company_id} • {Math.round(run.latency_ms || 0)}ms</p>
              </button>
            ))}
          </CardContent>
        </Card>

        <Card className="xl:col-span-2">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Activity className="w-4 h-4" />
              ReAct Trace Timeline
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {!selectedRun && <p className="text-sm text-muted-foreground">Select or create a run to inspect traces.</p>}
            {selectedRun?.traces.map((trace) => (
              <div key={trace.id} className="border rounded-md p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <Badge variant="outline">{trace.agent_name}</Badge>
                    <span className="text-xs text-muted-foreground">{trace.step_type}</span>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    {Math.round(trace.latency_ms)}ms • {trace.tokens_used} tokens • ${trace.cost_usd.toFixed(6)}
                  </span>
                </div>
                <p className="text-sm mt-2">{trace.thought}</p>
                {trace.decision && <p className="text-xs text-muted-foreground mt-1">{trace.decision}</p>}
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4" />
              Eval Dashboard
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <Button variant="outline" size="sm" onClick={rerunEvals} disabled={!selectedRun}>
              Run Evals
            </Button>
            {selectedRun?.evals.map((item) => (
              <div key={item.metric_name} className="flex items-center justify-between rounded-md border p-2">
                <span className="text-sm">{item.metric_name}</span>
                <Badge variant={item.passed ? "default" : "destructive"}>{Math.round(item.score * 100)}%</Badge>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Sparkles className="w-4 h-4" />
              Recommendations
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {recommendations.slice(0, 4).map((rec) => (
              <div key={rec.id} className="rounded-md border p-3">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-medium">{rec.title}</p>
                  <Badge variant="outline">{Math.round(rec.confidence_score * 100)}%</Badge>
                </div>
                <p className="text-xs text-muted-foreground mt-1">{rec.reasoning}</p>
              </div>
            ))}
            {recommendations.length === 0 && <p className="text-sm text-muted-foreground">Run an agent cycle to create recommendations.</p>}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Database className="w-4 h-4" />
              Data Sources
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {sources.map((source) => (
              <div key={source.id} className="flex items-center justify-between rounded-md border p-2">
                <div>
                  <p className="text-sm font-medium">{source.name}</p>
                  <p className="text-xs text-muted-foreground">{source.source_type} • {source.status}</p>
                </div>
                <Button variant="outline" size="sm" onClick={() => syncPipeline(source.id)} disabled={loading}>
                  Pipeline
                </Button>
                <Button variant="outline" size="sm" onClick={() => runBeam(source.id)} disabled={loading}>
                  Beam
                </Button>
                <Button variant="outline" size="sm" onClick={() => runSpark(source.id)} disabled={loading}>
                  Spark
                </Button>
                <Button variant="outline" size="sm" onClick={() => testSource(source.id)}>
                  Test
                </Button>
                <Button variant="outline" size="sm" onClick={() => syncSource(source.id)} disabled={loading}>
                  Sync
                </Button>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <ShieldCheck className="w-4 h-4" />
            Secure MCP-Style Tools
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="flex flex-wrap gap-2">
            {["get_company_financials", "get_kpi_risks", "run_forecast", "run_scenario", "generate_board_pack", "create_budget_recommendation"].map(
              (tool) => (
                <Button key={tool} variant="outline" size="sm" onClick={() => runTool(tool)}>
                  <Wrench className="w-3.5 h-3.5 mr-2" />
                  {tool}
                </Button>
              ),
            )}
          </div>
          {toolResult && (
            <pre className="w-full lg:w-[420px] overflow-auto rounded-md bg-muted p-3 text-xs">
              {JSON.stringify(toolResult, null, 2)}
            </pre>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
