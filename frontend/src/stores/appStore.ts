import { create } from "zustand";

export type CompanyId =
  | "cloudcrm"
  | "manufacturetech"
  | "healthcaretech"
  | "ecommerce"
  | "fintech"
  | "industrial";

export interface PortfolioCompany {
  id: CompanyId;
  name: string;
  sector: string;
  arr: number;
  revenue: number;
  ebitda: number;
  ebitdaMargin: number;
  budgetVariance: number;
  forecastVariance: number;
  status: "on-track" | "at-risk" | "off-track";
  growthRate: number;
  employees: number;
  description: string;
  apiId: number;
}

export interface AgentActivity {
  id: string;
  agentName: string;
  action: string;
  company?: string;
  timestamp: Date;
  status: "running" | "completed" | "alert" | "error";
  detail?: string;
}

export interface KpiData {
  name: string;
  category: string;
  actual: number;
  target: number;
  unit: string;
  trend: number[];
  status: "green" | "yellow" | "red";
  variance: number;
  companyId: CompanyId;
}

export interface ScenarioAssumptions {
  revenueGrowth: number;
  grossMargin: number;
  headcountGrowth: number;
  churnRate: number;
  priceIncrease: number;
  opexGrowth: number;
}

export interface EmailTemplate {
  id: string;
  name: string;
  subject: string;
  type: "alert" | "report" | "insight" | "summary";
  lastSent?: Date;
  recipients: string[];
  status: "active" | "draft" | "paused";
}

export interface SendLog {
  id: string;
  templateId: string;
  templateName: string;
  sentAt: Date;
  recipients: string[];
  status: "delivered" | "failed" | "pending";
  agentName: string;
}

interface AppState {
  theme: "light" | "dark";
  toggleTheme: () => void;

  selectedCompany: CompanyId | null;
  setSelectedCompany: (id: CompanyId | null) => void;

  companies: PortfolioCompany[];
  setCompanies: (c: PortfolioCompany[]) => void;

  agentActivities: AgentActivity[];
  addAgentActivity: (a: AgentActivity) => void;

  kpis: KpiData[];
  setKpis: (k: KpiData[]) => void;

  scenarioAssumptions: {
  base: ScenarioAssumptions;
  upside: ScenarioAssumptions;
  downside: ScenarioAssumptions;
};
  updateAssumption: (
  scenario: "base" | "upside" | "downside",
  key: keyof ScenarioAssumptions,
  value: number
) => void;

  emailTemplates: EmailTemplate[];
  sendLogs: SendLog[];
  addSendLog: (l: SendLog) => void;

  isConnected: boolean;
  setConnected: (v: boolean) => void;

  loadingCompanies: boolean;
  setLoadingCompanies: (v: boolean) => void;
}

export const useAppStore = create<AppState>((set) => ({
  theme: "dark",
  toggleTheme: () =>
    set((s) => {
      const next = s.theme === "dark" ? "light" : "dark";
      document.documentElement.classList.toggle("dark", next === "dark");
      return { theme: next };
    }),

  selectedCompany: null,
  setSelectedCompany: (id) => set({ selectedCompany: id }),

  companies: [],
  setCompanies: (companies) => set({ companies }),

  agentActivities: [],
  addAgentActivity: (a) =>
    set((s) => ({
      agentActivities: [a, ...s.agentActivities].slice(0, 50),
    })),

  kpis: [],
  setKpis: (kpis) => set({ kpis }),

  scenarioAssumptions: {
  base: {
    revenueGrowth: 15,
    grossMargin: 72,
    headcountGrowth: 10,
    churnRate: 2.5,
    priceIncrease: 5,
    opexGrowth: 8,
  },
  upside: {
    revenueGrowth: 25,
    grossMargin: 76,
    headcountGrowth: 15,
    churnRate: 1.5,
    priceIncrease: 8,
    opexGrowth: 12,
  },
  downside: {
    revenueGrowth: 5,
    grossMargin: 65,
    headcountGrowth: 2,
    churnRate: 5,
    priceIncrease: 0,
    opexGrowth: 4,
  },
},

  updateAssumption: (scenario, key, value) =>
    set((s) => ({
      scenarioAssumptions: {
        ...s.scenarioAssumptions,
        [scenario]: {
          ...s.scenarioAssumptions[scenario],
          [key]: value,
        },
      },
    })),

  emailTemplates: [],
  sendLogs: [],
  addSendLog: (l) =>
    set((s) => ({
      sendLogs: [l, ...s.sendLogs],
    })),

  isConnected: false,
  setConnected: (v) => set({ isConnected: v }),

  loadingCompanies: false,
  setLoadingCompanies: (v) => set({ loadingCompanies: v }),
}));
