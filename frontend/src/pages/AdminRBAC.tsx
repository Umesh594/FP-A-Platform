import { useEffect, useState } from "react";
import { ShieldCheck } from "lucide-react";
import { api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function AdminRBAC() {
  const [roles, setRoles] = useState<Array<{ role: string; permissions: string[] }>>([]);

  useEffect(() => {
    api.getAuthRoles().then(setRoles).catch(() => setRoles([]));
  }, []);

  return (
    <div className="p-6 space-y-6 animate-fade-up">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Admin / RBAC</h1>
        <p className="text-sm text-muted-foreground mt-1">
          OAuth-compatible bearer auth, finance roles, secure tool permissions, and audit-first access control.
        </p>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {roles.map((item) => (
          <Card key={item.role}>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <ShieldCheck className="w-4 h-4" />
                {item.role}
              </CardTitle>
            </CardHeader>
            <CardContent className="flex flex-wrap gap-2">
              {item.permissions.map((permission) => (
                <Badge key={permission} variant="outline">
                  {permission}
                </Badge>
              ))}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
