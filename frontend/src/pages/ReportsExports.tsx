import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  BoardPackPreview,
  DataRoomFile,
  exportReport,
  generateBoardPack,
  getBoardPackPreview,
  getDataRoomFiles,
} from "@/api/client";
import { FileText, Download, Table, FileSpreadsheet, FolderOpen, Eye, Loader2, Lock } from "lucide-react";

const exportCards = [
  { title: "Portfolio Companies", description: "Company master data from seeded backend", exportType: "companies" },
  { title: "Historical Financial Metrics", description: "36 months of P&L metrics for all companies", exportType: "financials" },
  { title: "KPI History", description: "Seeded KPI actuals and targets", exportType: "kpis" },
  { title: "Strategic Initiatives", description: "Initiative business cases and ROI inputs", exportType: "initiatives" },
];

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

export default function ReportsExports() {
  const [preview, setPreview] = useState<BoardPackPreview | null>(null);
  const [files, setFiles] = useState<DataRoomFile[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    getBoardPackPreview().then(setPreview).catch(() => setMessage("Could not load report preview"));
    getDataRoomFiles().then(setFiles).catch(() => setMessage("Could not load data room files"));
  }, []);

  async function handleBoardPack() {
    setBusy("board-pack");
    setMessage(null);
    try {
      const blob = await generateBoardPack();
      downloadBlob(blob, "board_pack.pdf");
      setMessage("Board pack generated from live backend data.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Board pack failed");
    } finally {
      setBusy(null);
    }
  }

  async function handleExport(exportType: string, filename: string) {
    setBusy(exportType);
    setMessage(null);
    try {
      const blob = await exportReport(exportType);
      downloadBlob(blob, filename);
      setMessage(`${filename} exported.`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Export failed");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="p-6 space-y-6 animate-fade-up">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Reports & Exports</h1>
          <p className="text-sm text-muted-foreground mt-1">Board packs, CSV exports, and data room files from backend seed data</p>
        </div>
        <Button className="gradient-primary text-primary-foreground" onClick={handleBoardPack} disabled={busy === "board-pack"}>
          {busy === "board-pack" ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Download className="w-4 h-4 mr-2" />}
          Generate Board Pack
        </Button>
      </div>

      {message && <div className="text-sm text-muted-foreground bg-secondary px-3 py-2 rounded-md">{message}</div>}

      <Tabs defaultValue="boardpack" className="space-y-4">
        <TabsList className="bg-secondary">
          <TabsTrigger value="boardpack"><FileText className="w-4 h-4 mr-1.5" />Board Pack</TabsTrigger>
          <TabsTrigger value="exports"><FileSpreadsheet className="w-4 h-4 mr-1.5" />CSV Exports</TabsTrigger>
          <TabsTrigger value="dataroom"><FolderOpen className="w-4 h-4 mr-1.5" />Data Room</TabsTrigger>
        </TabsList>

        <TabsContent value="boardpack">
          <Card className="glass-card">
            <CardHeader>
              <CardTitle className="text-base">{preview?.title || "Monthly Board Pack"}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                <div className="p-3 rounded-lg bg-secondary/50">
                  <div className="text-xs text-muted-foreground">Companies</div>
                  <div className="text-xl font-bold">{preview?.companies ?? "-"}</div>
                </div>
                <div className="p-3 rounded-lg bg-secondary/50">
                  <div className="text-xs text-muted-foreground">Revenue</div>
                  <div className="text-xl font-bold">${(((preview?.total_revenue || 0) / 1_000_000).toFixed(1))}M</div>
                </div>
                <div className="p-3 rounded-lg bg-secondary/50">
                  <div className="text-xs text-muted-foreground">EBITDA</div>
                  <div className="text-xl font-bold">${(((preview?.total_ebitda || 0) / 1_000_000).toFixed(1))}M</div>
                </div>
                <div className="p-3 rounded-lg bg-secondary/50">
                  <div className="text-xs text-muted-foreground">Margin</div>
                  <div className="text-xl font-bold">{(((preview?.ebitda_margin || 0) * 100).toFixed(1))}%</div>
                </div>
              </div>

              <div className="space-y-2">
                {(preview?.sections || []).map((section) => (
                  <div key={section} className="flex items-center justify-between p-3 rounded-lg border border-border">
                    <div className="flex items-center gap-3">
                      <FileText className="w-4 h-4 text-muted-foreground" />
                      <span className="text-sm text-foreground">{section}</span>
                    </div>
                    <Badge>ready</Badge>
                  </div>
                ))}
              </div>

              <div className="flex gap-2 pt-2 border-t border-border">
                <Button variant="outline" size="sm" onClick={() => getBoardPackPreview().then(setPreview)}>
                  <Eye className="w-3.5 h-3.5 mr-1.5" />Refresh Preview
                </Button>
                <Button size="sm" onClick={handleBoardPack} disabled={busy === "board-pack"}>
                  <Download className="w-3.5 h-3.5 mr-1.5" />Download PDF
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="exports">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {exportCards.map((exp) => (
              <Card key={exp.exportType} className="glass-card">
                <CardContent className="pt-5">
                  <div className="w-10 h-10 rounded-lg bg-success/10 flex items-center justify-center">
                    <Table className="w-5 h-5 text-success" />
                  </div>
                  <h3 className="text-sm font-semibold text-foreground mt-3">{exp.title}</h3>
                  <p className="text-xs text-muted-foreground mt-1 min-h-10">{exp.description}</p>
                  <Button
                    variant="outline"
                    size="sm"
                    className="mt-4 w-full"
                    onClick={() => handleExport(exp.exportType, `${exp.exportType}.csv`)}
                    disabled={busy === exp.exportType}
                  >
                    {busy === exp.exportType ? <Loader2 className="w-3 h-3 mr-1 animate-spin" /> : <Download className="w-3 h-3 mr-1" />}
                    Export CSV
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="dataroom">
          <Card className="glass-card overflow-hidden">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">Secure Data Room</CardTitle>
                <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <Lock className="w-3 h-3" />
                  Backend generated exports
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left text-xs font-medium text-muted-foreground p-3">File</th>
                    <th className="text-left text-xs font-medium text-muted-foreground p-3">Category</th>
                    <th className="text-right text-xs font-medium text-muted-foreground p-3">Source</th>
                    <th className="text-right text-xs font-medium text-muted-foreground p-3"></th>
                  </tr>
                </thead>
                <tbody>
                  {files.map((f) => (
                    <tr key={f.id} className="border-b border-border/50 hover:bg-secondary/50 transition-colors">
                      <td className="p-3 flex items-center gap-2">
                        <FileText className="w-4 h-4 text-primary shrink-0" />
                        <span className="text-sm text-foreground">{f.name}</span>
                      </td>
                      <td className="p-3"><Badge variant="secondary" className="text-xs">{f.category}</Badge></td>
                      <td className="p-3 text-right text-sm text-muted-foreground">{f.uploaded}</td>
                      <td className="p-3 text-right">
                        <Button variant="ghost" size="sm" onClick={() => handleExport(f.export_type, f.name)}>
                          <Download className="w-3.5 h-3.5" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
