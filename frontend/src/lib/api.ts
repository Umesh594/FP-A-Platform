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