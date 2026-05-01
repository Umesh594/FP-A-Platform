const BASE_URL =
  import.meta.env.VITE_API_URL ||
  import.meta.env.VITE_API_BASE_URL ||
  "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`API ${res.status}: ${err}`);
  }

  if (res.status === 204) return {} as T;
  return res.json();
}

async function requestBlob(path: string, options?: RequestInit): Promise<Blob> {
  const res = await fetch(`${BASE_URL}${path}`, options);
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`API ${res.status}: ${err}`);
  }
  return res.blob();
}

export interface ApiCompany {
  id: number;
  name: string;
  sector: string;
  revenue: number;
  employees: number;
  ebitda: number;
  arr: number;
}

export const getCompanies = () => request<ApiCompany[]>("/companies/");

export interface FinancialHistory {
  period: string;
  revenue: number;
  cogs: number;
  gross_profit: number;
  ebitda: number;
}

export interface FinancialForecast {
  revenue_forecast: { ds: string; yhat: number; yhat_lower: number; yhat_upper: number }[];
  expense_forecast: { ds: string; yhat: number; yhat_lower: number; yhat_upper: number }[];
}

export const getFinancialHistory = (companyId: number) =>
  request<FinancialHistory[]>(`/financials/${companyId}/history`);

export const getFinancialForecast = (companyId: number) =>
  request<FinancialForecast>(`/financials/${companyId}/forecast`);

export interface ApiKpi {
  company_id?: number;
  name: string;
  actual: number;
  target: number;
  status: string;
}

export const getKpis = (companyId: number) =>
  request<ApiKpi[]>(`/kpis/${companyId}`);

export const getAllKpis = () => request<ApiKpi[]>("/kpis/");

export interface ScenarioResult {
  agent: string;
  scenarios: {
    optimistic: Record<string, { mean: number; min: number; max: number }>;
    base: Record<string, { mean: number; min: number; max: number }>;
    pessimistic: Record<string, { mean: number; min: number; max: number }>;
  };
}

export const getScenarios = (baseRevenue: number, baseExpense: number) =>
  request<ScenarioResult>(
    `/scenarios/?base_revenue=${encodeURIComponent(baseRevenue)}&base_expense=${encodeURIComponent(baseExpense)}`
  );

export interface VarianceResult {
  agent: string;
  variance: number;
  percentage: number;
  explanation: string;
}

export const getVariance = (companyId: number, period: string) =>
  request<VarianceResult>(`/variances/${companyId}/${period}`);

export interface ApiInitiative {
  id: number;
  company_id: number;
  name: string;
  description?: string;
  investment: number;
  revenue_impact: number;
  start_date?: string;
}

export const getInitiatives = (companyId: number) =>
  request<ApiInitiative[]>(`/initiatives/${companyId}`);

export const createInitiative = (data: Omit<ApiInitiative, "id">) =>
  request<ApiInitiative>("/initiatives/", { method: "POST", body: JSON.stringify(data) });

export interface ApiDriver {
  period: string;
  customer_count: number | null;
  price_per_customer: number | null;
}

export const getDrivers = (companyId: number) =>
  request<ApiDriver[]>(`/drivers/${companyId}`);

export interface EmailTemplateDto {
  id: string;
  name: string;
  subject: string;
  type: "alert" | "report" | "insight" | "summary";
  recipients: string[];
  status: "active" | "draft" | "paused";
}

export interface SendLogDto {
  id: string;
  templateId: string;
  templateName: string;
  sentAt: string;
  recipients: string[];
  status: "delivered" | "failed" | "pending";
  agentName: string;
}

export const getEmailTemplates = () => request<EmailTemplateDto[]>("/emails/templates");
export const getEmailLogs = () => request<SendLogDto[]>("/emails/logs");

export const sendEmail = (payload: { to_email: string; subject: string; html_content: string }) =>
  request<{ status: string }>("/emails/send", { method: "POST", body: JSON.stringify(payload) });

export interface BoardPackPreview {
  title: string;
  companies: number;
  total_revenue: number;
  total_ebitda: number;
  ebitda_margin: number;
  sections: string[];
}

export interface DataRoomFile {
  id: string;
  name: string;
  category: string;
  size: string;
  uploaded: string;
  export_type: string;
}

export const getBoardPackPreview = () => request<BoardPackPreview>("/reports/board-pack/preview");
export const generateBoardPack = () => requestBlob("/reports/board-pack", { method: "POST" });
export const exportReport = (exportType: string) => requestBlob(`/reports/exports/${exportType}`);
export const getDataRoomFiles = () => request<DataRoomFile[]>("/reports/dataroom/files");

export const runPlanningCycle = (companyId: number, notifyEmail?: string) => {
  const params = notifyEmail ? `?notify_email=${encodeURIComponent(notifyEmail)}` : "";
  return request<Record<string, unknown>>(`/orchestrator/run/${companyId}${params}`, { method: "POST" });
};
