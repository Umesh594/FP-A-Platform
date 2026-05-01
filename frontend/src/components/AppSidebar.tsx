import {
  LayoutDashboard,
  Building2,
  GitBranch,
  BarChart3,
  FileText,
  Mail,
  Sun,
  Moon,
  Activity,
  Wifi,
  WifiOff,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { NavLink } from "@/components/NavLink";
import { useLocation } from "react-router-dom";
import { useAppStore } from "@/stores/appStore";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarFooter,
  SidebarHeader,
  useSidebar,
} from "@/components/ui/sidebar";

export function AppSidebar() {
  const { state, toggleSidebar } = useSidebar();
  const { selectedCompany, theme, toggleTheme, isConnected } = useAppStore();
  const collapsed = state === "collapsed";
  const location = useLocation();
  const navItems = [
  { title: "Portfolio Dashboard", url: "/", icon: LayoutDashboard },
  {
    title: "Company Detail",
    url: selectedCompany ? `/company/${selectedCompany}` : "/company",
    icon: Building2,
  },
  { title: "Scenario Builder", url: "/scenarios", icon: GitBranch },
  { title: "KPI Scorecard", url: "/kpis", icon: BarChart3 },
  { title: "Reports & Exports", url: "/reports", icon: FileText },
  { title: "Email Center", url: "/emails", icon: Mail },
];

  return (
    <Sidebar collapsible="icon" className="border-r border-sidebar-border">
      <SidebarHeader className="p-4">
        {!collapsed ? (
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg gradient-primary flex items-center justify-center">
              <Activity className="w-4 h-4 text-primary-foreground" />
            </div>
            <div className="flex flex-col">
              <span className="text-sm font-semibold text-sidebar-accent-foreground">Summit Growth</span>
              <span className="text-[10px] text-sidebar-foreground">FP&A Platform</span>
            </div>
          </div>
        ) : (
          <div className="w-8 h-8 rounded-lg gradient-primary flex items-center justify-center mx-auto">
            <Activity className="w-4 h-4 text-primary-foreground" />
          </div>
        )}
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel className="text-[10px] uppercase tracking-widest text-sidebar-foreground/60">
            {!collapsed && "Navigation"}
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {navItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild>
                    <NavLink
                      to={item.url}
                      end={item.url === "/"}
                      className="flex items-center gap-3 px-3 py-2 rounded-md text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-colors"
                      activeClassName="bg-sidebar-accent text-sidebar-primary font-medium"
                    >
                      <item.icon className="w-4 h-4 shrink-0" />
                      {!collapsed && <span className="text-sm">{item.title}</span>}
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        {!collapsed && (
          <SidebarGroup>
            <SidebarGroupLabel className="text-[10px] uppercase tracking-widest text-sidebar-foreground/60">
              Agent Status
            </SidebarGroupLabel>
            <SidebarGroupContent>
              <div className="px-3 space-y-2">
                {[
                  { name: "Strategic Orchestrator", status: "active" },
                  { name: "Revenue Forecasting", status: "active" },
                  { name: "KPI Tracking", status: "active" },
                  { name: "Variance Analysis", status: "idle" },
                  { name: "Scenario Modeling", status: "active" },
                ].map((agent) => (
                  <div key={agent.name} className="flex items-center gap-2 text-xs">
                    <div className={agent.status === "active" ? "status-dot-green animate-pulse-glow" : "status-dot-yellow"} />
                    <span className="text-sidebar-foreground/80 truncate">{agent.name}</span>
                  </div>
                ))}
              </div>
            </SidebarGroupContent>
          </SidebarGroup>
        )}
      </SidebarContent>

      <SidebarFooter className="p-3 space-y-2">
        <div className="flex items-center justify-between px-1">
          <button onClick={toggleTheme} className="p-1.5 rounded-md hover:bg-sidebar-accent text-sidebar-foreground transition-colors">
            {theme === "dark" ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>
          <div className="flex items-center gap-1.5 text-xs text-sidebar-foreground/60">
            {isConnected ? <Wifi className="w-3 h-3 text-success" /> : <WifiOff className="w-3 h-3 text-destructive" />}
            {!collapsed && <span>{isConnected ? "Connected" : "Offline"}</span>}
          </div>
          <button onClick={toggleSidebar} className="p-1.5 rounded-md hover:bg-sidebar-accent text-sidebar-foreground transition-colors">
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>
      </SidebarFooter>
    </Sidebar>
  );
}
