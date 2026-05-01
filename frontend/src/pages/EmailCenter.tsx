import { useEffect, useState } from "react";
import { getEmailLogs, getEmailTemplates, sendEmail, EmailTemplateDto, SendLogDto } from "@/api/client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Mail, Send, Eye, Clock, CheckCircle, XCircle, AlertCircle, Users, Loader2 } from "lucide-react";
import { format } from "date-fns";

function renderTemplateBody(template: EmailTemplateDto) {
  if (template.type === "summary") {
    return "<h2>Weekly Portfolio Performance Summary</h2><p>This summary is generated from the backend FP&A portfolio dataset and autonomous monitoring workflow.</p>";
  }
  if (template.type === "alert") {
    return "<h2>KPI Threshold Alert</h2><p>An autonomous agent detected a KPI variance requiring review.</p>";
  }
  if (template.type === "report") {
    return "<h2>Monthly Board Pack Ready</h2><p>The latest backend-generated board pack is ready for review.</p>";
  }
  return "<h2>FP&A Insight</h2><p>A new autonomous FP&A insight is available.</p>";
}

export default function EmailCenter() {
  const [templates, setTemplates] = useState<EmailTemplateDto[]>([]);
  const [logs, setLogs] = useState<SendLogDto[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<EmailTemplateDto | null>(null);
  const [sending, setSending] = useState(false);
  const [sendStatus, setSendStatus] = useState<"idle" | "ok" | "err">("idle");
  const [previewOpen, setPreviewOpen] = useState(true);

  useEffect(() => {
    getEmailTemplates().then((items) => {
      setTemplates(items);
      setSelectedTemplate(items[0] || null);
    });
    getEmailLogs().then(setLogs);
  }, []);

  async function handleTestSend() {
    if (!selectedTemplate) return;
    setSending(true);
    setSendStatus("idle");
    try {
      await sendEmail({
        to_email: selectedTemplate.recipients[0],
        subject: selectedTemplate.subject,
        html_content: renderTemplateBody(selectedTemplate),
      });
      setLogs(await getEmailLogs());
      setSendStatus("ok");
    } catch {
      setSendStatus("err");
    } finally {
      setSending(false);
      setTimeout(() => setSendStatus("idle"), 3000);
    }
  }

  if (!selectedTemplate) {
    return <div className="p-6 text-sm text-muted-foreground">Loading backend email templates...</div>;
  }

  return (
    <div className="p-6 space-y-6 animate-fade-up">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Email Center</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Backend-driven automated email templates, recipients, and delivery logs
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="secondary" className="gap-1">
            <Send className="w-3 h-3" />{logs.length} emails sent
          </Badge>
          <Badge variant="default" className="gap-1">
            <Mail className="w-3 h-3" />{templates.filter((t) => t.status === "active").length} active templates
          </Badge>
        </div>
      </div>

      <Tabs defaultValue="templates" className="space-y-4">
        <TabsList className="bg-secondary">
          <TabsTrigger value="templates"><Mail className="w-4 h-4 mr-1.5" />Templates</TabsTrigger>
          <TabsTrigger value="logs"><Clock className="w-4 h-4 mr-1.5" />Send Log</TabsTrigger>
          <TabsTrigger value="recipients"><Users className="w-4 h-4 mr-1.5" />Recipients</TabsTrigger>
        </TabsList>

        <TabsContent value="templates">
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
            <div className="lg:col-span-2 space-y-2">
              {templates.map((t) => (
                <Card
                  key={t.id}
                  className={`glass-card cursor-pointer transition-all hover:metric-glow ${selectedTemplate.id === t.id ? "ring-1 ring-primary" : ""}`}
                  onClick={() => setSelectedTemplate(t)}
                >
                  <CardContent className="py-3 px-4">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-foreground">{t.name}</span>
                      <Badge variant={t.status === "active" ? "default" : "secondary"} className="text-xs">
                        {t.status}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground truncate">{t.subject}</p>
                    <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
                      <Badge variant="outline" className="text-xs">{t.type}</Badge>
                      <span>{t.recipients.length} recipients</span>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            <div className="lg:col-span-3">
              <Card className="glass-card">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base">Preview: {selectedTemplate.name}</CardTitle>
                    <div className="flex gap-2 items-center">
                      {sendStatus === "ok" && <span className="text-xs text-success">Sent</span>}
                      {sendStatus === "err" && <span className="text-xs text-destructive">Failed</span>}
                      <Button variant="outline" size="sm" onClick={() => setPreviewOpen((v) => !v)}>
                        <Eye className="w-3.5 h-3.5 mr-1.5" />{previewOpen ? "Hide" : "Preview"}
                      </Button>
                      <Button size="sm" onClick={handleTestSend} disabled={sending}>
                        {sending ? <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" /> : <Send className="w-3.5 h-3.5 mr-1.5" />}
                        Test Send
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                {previewOpen && (
                  <CardContent>
                    <div className="rounded-lg border border-border bg-card p-6 space-y-4">
                      <div className="space-y-3">
                        <div className="flex gap-2 text-xs"><span className="text-muted-foreground w-16">From:</span><span>FP&A Platform</span></div>
                        <div className="flex gap-2 text-xs"><span className="text-muted-foreground w-16">To:</span><span>{selectedTemplate.recipients.join(", ")}</span></div>
                        <div className="flex gap-2 text-xs"><span className="text-muted-foreground w-16">Subject:</span><span>{selectedTemplate.subject}</span></div>
                      </div>
                      <div className="border-t border-border pt-4 text-sm text-muted-foreground" dangerouslySetInnerHTML={{ __html: renderTemplateBody(selectedTemplate) }} />
                    </div>
                  </CardContent>
                )}
              </Card>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="logs">
          <Card className="glass-card overflow-hidden">
            <CardHeader><CardTitle className="text-base">Send Log</CardTitle></CardHeader>
            <CardContent>
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border">
                    {["Status", "Template", "Agent", "Recipients", "Sent At"].map((h, i) => (
                      <th key={h} className={`text-xs font-medium text-muted-foreground p-3 ${i === 4 ? "text-right" : "text-left"}`}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {logs.map((log) => (
                    <tr key={log.id} className="border-b border-border/50 hover:bg-secondary/50 transition-colors">
                      <td className="p-3">
                        {log.status === "delivered" && <CheckCircle className="w-4 h-4 text-success" />}
                        {log.status === "failed" && <XCircle className="w-4 h-4 text-destructive" />}
                        {log.status === "pending" && <AlertCircle className="w-4 h-4 text-warning" />}
                      </td>
                      <td className="p-3 text-sm text-foreground">{log.templateName}</td>
                      <td className="p-3"><Badge variant="secondary" className="text-xs">{log.agentName}</Badge></td>
                      <td className="p-3 text-xs text-muted-foreground">{log.recipients.join(", ")}</td>
                      <td className="p-3 text-right text-xs text-muted-foreground">{format(new Date(log.sentAt), "MMM d, yyyy h:mm a")}</td>
                    </tr>
                  ))}
                  {logs.length === 0 && (
                    <tr><td className="p-4 text-sm text-muted-foreground" colSpan={5}>No backend send events yet.</td></tr>
                  )}
                </tbody>
              </table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="recipients">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {templates.map((t) => (
              <Card key={t.id} className="glass-card">
                <CardContent className="pt-5">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-sm font-semibold text-foreground">{t.name}</h3>
                    <Badge variant="secondary">{t.type}</Badge>
                  </div>
                  <div className="space-y-1.5">
                    {t.recipients.map((e) => (
                      <div key={e} className="flex items-center gap-2 text-xs text-muted-foreground">
                        <Mail className="w-3 h-3" />{e}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
