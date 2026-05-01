import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface Props {
  drivers: Record<string, number>;
}

export function DriverDashboard({ drivers }: Props) {
  const driverItems = [
    { label: "Total Customers", value: drivers.totalCustomers?.toLocaleString(), unit: "" },
    { label: "New Customers / Month", value: drivers.newCustomersPerMonth, unit: "" },
    { label: "Avg Contract Value", value: `$${drivers.avgContractValue?.toLocaleString()}`, unit: "" },
    { label: "Net Revenue Retention", value: drivers.netRevenueRetention, unit: "%" },
    { label: "Gross Churn Rate", value: drivers.grossChurn, unit: "%" },
    { label: "Expansion Revenue", value: drivers.expansionRevenue, unit: "%" },
    { label: "Avg Sales Price / mo", value: `$${drivers.avgSalesPrice?.toLocaleString()}`, unit: "" },
  ];

  return (
    <Card className="glass-card">
      <CardHeader>
        <CardTitle className="text-base">Revenue Drivers — Key Assumptions</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {driverItems.map((d, i) => (
            <div key={i} className="p-4 rounded-lg bg-secondary/50 border border-border">
              <div className="text-xs text-muted-foreground mb-1">{d.label}</div>
              <div className="text-xl font-bold font-mono text-foreground">
                {d.value}{d.unit}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
