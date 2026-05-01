from agno.agent import Agent
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.financials import FinancialMetric
from app.models.kpi import KPI
from app.models.initiative import Initiative


class ReportingAgent(Agent):
    def __init__(self):
        super().__init__()
        self.name = "Reporting & Insights Agent"

    def generate_board_pack(self, filename: str, db: Session):
        styles = getSampleStyleSheet()
        doc = SimpleDocTemplate(filename)
        flow = []

        companies = db.query(Company).all()

        for company in companies:
            # 🏢 Company Header
            flow.append(Paragraph(f"<b>{company.name}</b>", styles["Heading2"]))
            flow.append(Spacer(1, 10))

            # 📊 FINANCIAL INSIGHTS
            rows = db.query(FinancialMetric).filter(
                FinancialMetric.company_id == company.id
            ).order_by(FinancialMetric.period).all()

            if len(rows) >= 2:
                first_rev = rows[0].revenue or 0
                last_rev = rows[-1].revenue or 0
                growth = ((last_rev - first_rev) / first_rev * 100) if first_rev else 0

                flow.append(Paragraph(
                    f"Revenue growth over period: {growth:.2f}%", styles["BodyText"]
                ))
            else:
                flow.append(Paragraph(
                    "Not enough financial data", styles["BodyText"]
                ))

            flow.append(Spacer(1, 8))

            # 📈 KPI INSIGHTS
            kpis = db.query(KPI).filter(
                KPI.company_id == company.id
            ).all()

            if kpis:
                kpi_table = [["KPI", "Actual", "Target", "Status"]]
                for k in kpis:
                    kpi_table.append([k.name, f"{k.actual:.2f}", f"{k.target:.2f}", k.status or ""])
                tbl = Table(kpi_table, hAlign="LEFT")
                tbl.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ]))
                flow.append(tbl)
            else:
                flow.append(Paragraph("No KPI data", styles["BodyText"]))

            flow.append(Spacer(1, 8))

            # 🚀 INITIATIVE INSIGHTS
            initiatives = db.query(Initiative).filter(
                Initiative.company_id == company.id
            ).all()

            for i in initiatives:
                roi = (i.revenue_impact / i.investment) if i.investment else 0

                flow.append(Paragraph(
                    f"Initiative {i.name}: ROI {roi:.2f}",
                    styles["BodyText"]
                ))

            flow.append(Spacer(1, 20))

        doc.build(flow)

        return filename
