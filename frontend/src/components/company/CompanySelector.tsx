import { CompanyId, PortfolioCompany } from "@/stores/appStore";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

interface Props {
  companies: PortfolioCompany[];
  selected: CompanyId;
  onSelect: (id: CompanyId) => void;
}

export function CompanySelector({ companies, selected, onSelect }: Props) {
  return (
    <Select value={selected} onValueChange={(v) => onSelect(v as CompanyId)}>
      <SelectTrigger className="w-56 bg-secondary">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {companies.map((c) => (
          <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
