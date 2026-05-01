import { useEffect, useState, useCallback } from "react";
import {
  getCompanies,
  getFinancialHistory,
  getFinancialForecast,
  getKpis,
  getAllKpis,
  getScenarios,
  getVariance,
  getInitiatives,
  getDrivers,
  ApiCompany,
  FinancialHistory,
  FinancialForecast,
  ApiKpi,
  ScenarioResult,
  VarianceResult,
  ApiInitiative,
  ApiDriver,
} from "@/api/client";

// Generic fetch hook
function useFetch<T>(fetcher: () => Promise<T>, deps: unknown[] = []) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetcher();
      setData(result);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => { load(); }, [load]);

  return { data, loading, error, refetch: load };
}

export function useCompanies() {
  return useFetch<ApiCompany[]>(() => getCompanies(), []);
}

export function useFinancialHistory(companyId: number | null) {
  return useFetch<FinancialHistory[]>(
    () => (companyId != null ? getFinancialHistory(companyId) : Promise.resolve([])),
    [companyId]
  );
}

export function useFinancialForecast(companyId: number | null) {
  return useFetch<FinancialForecast>(
    () =>
      companyId != null
        ? getFinancialForecast(companyId)
        : Promise.resolve({ revenue_forecast: [], expense_forecast: [] }),
    [companyId]
  );
}

export function useKpis(companyId: number | null) {
  return useFetch<ApiKpi[]>(
    () => (companyId != null ? getKpis(companyId) : getAllKpis()),
    [companyId]
  );
}

export function useScenarios(baseRevenue: number, baseExpense: number) {
  return useFetch<ScenarioResult>(
    () => getScenarios(baseRevenue, baseExpense),
    [baseRevenue, baseExpense]
  );
}

export function useVariance(companyId: number | null, period: string | null) {
  return useFetch<VarianceResult>(
    () =>
      companyId != null && period
        ? getVariance(companyId, period)
        : Promise.resolve({ agent: "", variance: 0, percentage: 0, explanation: "" }),
    [companyId, period]
  );
}

export function useInitiatives(companyId: number | null) {
  return useFetch<ApiInitiative[]>(
    () => (companyId != null ? getInitiatives(companyId) : Promise.resolve([])),
    [companyId]
  );
}

export function useDrivers(companyId: number | null) {
  return useFetch<ApiDriver[]>(
    () => (companyId != null ? getDrivers(companyId) : Promise.resolve([])),
    [companyId]
  );
}
