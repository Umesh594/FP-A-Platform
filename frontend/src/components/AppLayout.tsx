import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/AppSidebar";
import { useAppStore } from "@/stores/appStore";
import { Bell, Search, X } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";

export function AppLayout({ children }: { children: React.ReactNode }) {
  const { isConnected, agentActivities, companies } = useAppStore();
  const [panel, setPanel] = useState<"notifications" | "profile" | null>(null);
  const [query, setQuery] = useState("");
  const matches = query.trim()
    ? companies.filter((c) => c.name.toLowerCase().includes(query.toLowerCase())).slice(0, 5)
    : [];

  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full">
        <AppSidebar />
        <div className="flex-1 flex flex-col min-w-0">
          <header className="h-14 flex items-center justify-between border-b border-border px-4 bg-card/50 backdrop-blur-sm sticky top-0 z-10">
            <div className="flex items-center gap-3">
              <SidebarTrigger className="text-muted-foreground hover:text-foreground" />
              <div className="hidden md:flex items-center gap-2 bg-secondary rounded-lg px-3 py-1.5 relative">
                <Search className="w-3.5 h-3.5 text-muted-foreground" />
                <input
                  type="text"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Search seeded portfolio companies..."
                  className="bg-transparent text-sm text-foreground placeholder:text-muted-foreground outline-none w-64"
                />
                {query && (
                  <button onClick={() => setQuery("")} title="Clear search">
                    <X className="w-3 h-3 text-muted-foreground" />
                  </button>
                )}
                {matches.length > 0 && (
                  <div className="absolute top-10 left-0 w-full rounded-md border border-border bg-card shadow-lg p-2 z-50">
                    {matches.map((company) => (
                      <Link
                        key={company.id}
                        to={`/company/${company.id}`}
                        onClick={() => setQuery("")}
                        className="block px-3 py-2 text-sm rounded hover:bg-secondary"
                      >
                        {company.name}
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <div className={isConnected ? "status-dot-green" : "status-dot-red"} />
                <span className="hidden sm:inline">10 Agents Active</span>
              </div>
              <button
                className="relative p-2 rounded-lg hover:bg-secondary text-muted-foreground transition-colors"
                onClick={() => setPanel(panel === "notifications" ? null : "notifications")}
                title="Notifications"
              >
                <Bell className="w-4 h-4" />
                <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-destructive" />
              </button>
              <button
                className="w-8 h-8 rounded-full gradient-primary flex items-center justify-center text-primary-foreground text-xs font-semibold"
                onClick={() => setPanel(panel === "profile" ? null : "profile")}
                title="Profile"
              >
                SG
              </button>
            </div>
          </header>

          {panel && (
            <div className="fixed top-16 right-4 z-50 w-80 rounded-md border border-border bg-card shadow-lg">
              <div className="flex items-center justify-between p-3 border-b border-border">
                <div className="text-sm font-semibold">{panel === "notifications" ? "Notifications" : "Profile"}</div>
                <button onClick={() => setPanel(null)} title="Close panel">
                  <X className="w-4 h-4 text-muted-foreground" />
                </button>
              </div>
              {panel === "notifications" ? (
                <div className="p-3 space-y-2 max-h-80 overflow-auto">
                  {(agentActivities.length
                    ? agentActivities
                    : [
                        {
                          id: "status",
                          agentName: "System",
                          action: "Autonomous FP&A stack is online",
                          status: "completed" as const,
                          timestamp: new Date(),
                        },
                        {
                          id: "data",
                          agentName: "Data Loader",
                          action: `${companies.length} seeded portfolio companies loaded`,
                          status: "completed" as const,
                          timestamp: new Date(),
                        },
                      ]
                  )
                    .slice(0, 8)
                    .map((item) => (
                      <div key={item.id} className="p-2 rounded bg-secondary/50">
                        <div className="text-xs font-medium">{item.agentName}</div>
                        <div className="text-xs text-muted-foreground">{item.action}</div>
                      </div>
                    ))}
                </div>
              ) : (
                <div className="p-3 space-y-3 text-sm">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full gradient-primary flex items-center justify-center text-primary-foreground font-semibold">
                      SG
                    </div>
                    <div>
                      <div className="font-medium">Summit Growth Partners</div>
                      <div className="text-xs text-muted-foreground">Autonomous FP&A workspace</div>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="p-2 rounded bg-secondary/50">
                      <div className="text-muted-foreground">Companies</div>
                      <div className="font-semibold">{companies.length}</div>
                    </div>
                    <div className="p-2 rounded bg-secondary/50">
                      <div className="text-muted-foreground">Agents</div>
                      <div className="font-semibold">10</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          <main className="flex-1 overflow-auto">{children}</main>
        </div>
      </div>
    </SidebarProvider>
  );
}
