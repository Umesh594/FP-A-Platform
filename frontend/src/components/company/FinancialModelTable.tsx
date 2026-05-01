import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export interface MonthlyFinancial {
  month: string;
  revenue: number;
  cogs: number;
  grossProfit: number;
  opex: number;
  ebitda: number;
  depreciation: number;
  ebit: number;
  forecast?: { revenue: number; ebitda: number };
  budget?: { revenue: number; ebitda: number };
}

interface Props {
  data: MonthlyFinancial[];
}

export function FinancialModelTable({ data }: Props) {
  const rows = [
    { label: "Revenue", key: "revenue" as const, bold: true },
    { label: "COGS", key: "cogs" as const },
    { label: "Gross Profit", key: "grossProfit" as const, bold: true },
    { label: "Operating Expenses", key: "opex" as const },
    { label: "EBITDA", key: "ebitda" as const, bold: true },
    { label: "D&A", key: "depreciation" as const },
    { label: "EBIT", key: "ebit" as const, bold: true },
  ];

  const total = (key: keyof MonthlyFinancial) =>
    data.reduce((s, d) => s + (d[key] as number), 0);

  return (
    <Card className="glass-card overflow-hidden">
      <CardHeader>
        <CardTitle className="text-base">
          Financial Model — Monthly P&L ($K)
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left p-3 font-medium text-muted-foreground sticky left-0 bg-card z-10 min-w-32">
                  Line Item
                </th>
                {data.map((d) => (
                  <th
                    key={d.month}
                    className="text-right p-3 font-medium text-muted-foreground min-w-20"
                  >
                    {d.month}
                  </th>
                ))}
                <th className="text-right p-3 font-semibold text-foreground min-w-24 bg-secondary/50">
                  FY Total
                </th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr
                  key={row.key}
                  className={`border-b border-border/30 ${
                    row.bold ? "bg-secondary/30" : ""
                  }`}
                >
                  <td
                    className={`p-3 sticky left-0 bg-card z-10 ${
                      row.bold
                        ? "font-semibold text-foreground"
                        : "text-muted-foreground pl-6"
                    }`}
                  >
                    {row.label}
                  </td>
                  {data.map((d) => (
                    <td
                      key={d.month}
                      className={`text-right p-3 font-mono ${
                        row.bold
                          ? "font-semibold text-foreground"
                          : "text-foreground"
                      }`}
                    >
                      {(d[row.key] as number).toLocaleString()}
                    </td>
                  ))}
                  <td className="text-right p-3 font-mono font-semibold text-foreground bg-secondary/50">
                    {total(row.key).toLocaleString()}
                  </td>
                </tr>
              ))}
              <tr className="border-b border-border/30">
                <td className="p-3 sticky left-0 bg-card z-10 text-muted-foreground italic">
                  EBITDA Margin
                </td>
                {data.map((d) => (
                  <td
                    key={d.month}
                    className="text-right p-3 font-mono text-muted-foreground italic"
                  >
                    {((d.ebitda / d.revenue) * 100).toFixed(1)}%
                  </td>
                ))}
                <td className="text-right p-3 font-mono font-semibold text-foreground bg-secondary/50">
                  {((total("ebitda") / total("revenue")) * 100).toFixed(1)}%
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}