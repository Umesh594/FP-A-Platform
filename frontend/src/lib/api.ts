export interface MonthlyFinancial {
  period: string;
  revenue: number;
  cogs: number;
  gross_profit: number;
  ebitda: number;
}

export interface ApiCompany {
  id: number;
  name: string;
  sector: string | null;
  revenue: number | null;
  employees: number | null;
  ebitda: number | null;
  arr: number | null;
}

export interface ApiFinancialHistory {
  period: string;
  revenue: number;
  cogs: number;
  gross_profit: number;
  ebitda: number;
}

export interface ApiForecastPoint {
  ds: string;
  yhat: number;
  yhat_lower: number;
  yhat_upper: number;
}

export interface ApiFinancialForecast {
  revenue_forecast?: ApiForecastPoint[];
  expense_forecast?: ApiForecastPoint[];
  error?: string;
}

export interface ApiKpi {
  name: string;
  actual: number;
  target: number;
  status: "green" | "yellow" | "red" | string;
}

export interface ApiDriver {
  period: string;
  customer_count: number | null;
  price_per_customer: number | null;
}

export interface ApiInitiative {
  id: number;
  name: string;
  description: string | null;
  company_id: number;
  investment: number | null;
  revenue_impact: number | null;
  start_date: string | null;
}

export interface ApiVariance {
  agent: string;
  variance: number;
  percentage: number;
  explanation: string;
  error?: string;
}

export interface ApiScenarioResponse {
  agent: string;
  scenarios: Record<
    string,
    Record<string, { mean: number; min: number; max: number }>
  >;
}

export interface AgentRunSummary {
  run_id: string;
  company_id: number;
  request_type: string;
  status: string;
  latency_ms: number;
  created_at: string;
  final_output?: Record<string, unknown>;
}

export interface AgentTrace {
  id: number;
  agent_name: string;
  step_type: string;
  thought: string;
  tool_name?: string;
  tool_input?: Record<string, unknown>;
  tool_output?: Record<string, unknown>;
  decision?: string;
  latency_ms: number;
  tokens_used: number;
  cost_usd: number;
  success: boolean;
  created_at: string;
}

export interface AgentEval {
  metric_name: string;
  score: number;
  passed: boolean;
  details?: Record<string, unknown>;
}

export interface AgentRunDetail {
  run: AgentRunSummary;
  traces: AgentTrace[];
  reflections: Array<{
    agent_name: string;
    critique: string;
    confidence_score: number;
    revised_output?: Record<string, unknown>;
  }>;
  evals: AgentEval[];
}

export interface Recommendation {
  id: number;
  company_id: number;
  recommendation_type: string;
  title: string;
  reasoning: string;
  confidence_score: number;
  expected_impact: string;
  status: string;
  created_at: string;
}

export interface DataSource {
  id: number;
  name: string;
  source_type: string;
  status: string;
  last_sync_at?: string | null;
}

export interface EmailPayload {
  to_email: string;
  subject: string;
  html_content: string;
}

const defaultBase = "http://localhost:8000";
const apiBase = import.meta.env.VITE_API_BASE_URL || defaultBase;

function getApiUrl(path: string) {
  const base = apiBase.replace(/\/$/, "");
  return `${base}${path}`;
}

export function getWsUrl() {
  const base = apiBase.replace(/\/$/, "");
  const url = new URL(base);
  const wsProtocol = url.protocol === "https:" ? "wss:" : "ws:";
  return `${wsProtocol}//${url.host}/ws/agents`;
}

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(getApiUrl(path), {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Request failed ${res.status}: ${text}`);
  }

  return (await res.json()) as T;
}

export const api = {
  async getCompanies() {
    return fetchJson<ApiCompany[]>("/companies/");
  },

  async getFinancialHistory(companyId: number) {
    return fetchJson<ApiFinancialHistory[]>(
      `/financials/${companyId}/history`
    );
  },

  async getFinancialForecast(companyId: number) {
    return fetchJson<ApiFinancialForecast>(
      `/financials/${companyId}/forecast`
    );
  },

  async getKpis(companyId: number) {
    return fetchJson<ApiKpi[]>(`/kpis/${companyId}`);
  },

  async getDrivers(companyId: number) {
    return fetchJson<ApiDriver[]>(`/drivers/${companyId}`);
  },

  async getInitiatives(companyId: number) {
    return fetchJson<ApiInitiative[]>(`/initiatives/${companyId}`);
  },

  async getVariances(companyId: number, period: string) {
    return fetchJson<ApiVariance>(
      `/variances/${companyId}/${period}`
    );
  },

  async getScenarios(baseRevenue: number, baseExpense: number) {
  return fetchJson<ApiScenarioResponse>(
    `/scenarios/?base_revenue=${encodeURIComponent(baseRevenue)}&base_expense=${encodeURIComponent(baseExpense)}`
  );
},

  async runAgentCycle(companyId: number) {
    return fetchJson<AgentRunSummary>("/agents/run-cycle", {
      method: "POST",
      body: JSON.stringify({ company_id: companyId, request_type: "planning_cycle" }),
    });
  },

  async getAgentRuns() {
    return fetchJson<AgentRunSummary[]>("/agents/runs");
  },

  async getAgentRun(runId: string) {
    return fetchJson<AgentRunDetail>(`/agents/runs/${encodeURIComponent(runId)}`);
  },

  async getObservabilitySummary() {
    return fetchJson<Record<string, number>>("/agents/observability/summary");
  },

  async getRecommendations() {
    return fetchJson<Recommendation[]>("/agents/recommendations");
  },

  async getDataSources() {
    return fetchJson<DataSource[]>("/agents/data-sources");
  },

  async runPipeline(sourceId?: number) {
    const suffix = sourceId ? `?source_id=${sourceId}` : "";
    return fetchJson<Record<string, unknown>>(`/agents/pipelines/run${suffix}`, {
      method: "POST",
      body: JSON.stringify({}),
    });
  },

  async testDataSource(sourceId: number) {
    return fetchJson<Record<string, unknown>>(`/agents/data-sources/${sourceId}/test`, {
      method: "POST",
      body: JSON.stringify({}),
    });
  },

  async syncDataSource(sourceId: number) {
    return fetchJson<Record<string, unknown>>(`/agents/data-sources/${sourceId}/sync`, {
      method: "POST",
      body: JSON.stringify({}),
    });
  },

  async getMcpServer() {
    return fetchJson<Record<string, unknown>>("/agents/mcp");
  },

  async getAuthRoles() {
    return fetchJson<Array<{ role: string; permissions: string[] }>>("/auth/roles");
  },

  async runEvals(runId: string) {
    return fetchJson<AgentEval[]>(`/agents/evals/${encodeURIComponent(runId)}`, {
      method: "POST",
      body: JSON.stringify({}),
    });
  },

  async executeSecureTool(toolName: string, companyId: number) {
    return fetchJson<Record<string, unknown>>("/agents/tools/execute", {
      method: "POST",
      body: JSON.stringify({
        tool_name: toolName,
        role: "Admin",
        tool_input: { company_id: companyId, user_id: "demo-user" },
      }),
    });
  },

  async sendEmail(payload: EmailPayload) {
    return fetchJson<{ status: string }>("/emails/send", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async generateBoardPack() {
    return fetchJson<{ file: string }>("/reports/board-pack", {
      method: "POST",
    });
  },
};
export const getCompanies = api.getCompanies;
export const getFinancialHistory = api.getFinancialHistory;
export const getFinancialForecast = api.getFinancialForecast;
export const getKpis = api.getKpis;
export const getDrivers = api.getDrivers;
export const getInitiatives = api.getInitiatives;
export const getVariance = api.getVariances;
export const getScenarios = api.getScenarios;
