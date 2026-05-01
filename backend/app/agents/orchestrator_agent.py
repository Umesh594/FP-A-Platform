import asyncio
import jinja2
import logging
from anyio import to_thread

from app.agents.revenue_agent import RevenueForecastAgent
from app.agents.expense_agent import ExpenseForecastAgent
from app.agents.initiative_agent import StrategicInitiativeAgent
from app.agents.capital_agent import CapitalPlanningAgent
from app.agents.kpi_agent import KPITrackingAgent
from app.agents.variance_agent import VarianceExplanationAgent
from app.agents.scenario_agent import ScenarioModelingAgent
from app.agents.budget_agent import BudgetBuilderAgent
from app.agents.reporting_agent import ReportingAgent

from app.services.email_service import send_email
from app.models.financials import FinancialMetric
from app.models.company import Company
from app.config import settings

logger = logging.getLogger(__name__)

class StrategicOrchestrator:
    def __init__(self):
        self.name = "Strategic Orchestrator"

    async def run_planning_cycle(self, company_id=None, company_name=None, db=None, notify_email: str = None):
        """
        Runs planning cycle. Supports both company_id (legacy) and company_name (new CSV).
        At least one of company_id or company_name must be provided.
        """
        if not company_id and not company_name:
            raise ValueError("Must provide at least company_id or company_name")
        if not db:
            raise ValueError("db session is required")

        if not company_id and company_name:
            company = db.query(Company).filter(Company.name == company_name).first()
            if company:
                company_id = company.id
        if not company_id:
            raise ValueError("company_id could not be resolved")

        # ------------------- Agents -------------------
        revenue_agent = RevenueForecastAgent()
        expense_agent = ExpenseForecastAgent()
        capital_agent = CapitalPlanningAgent()
        kpi_agent = KPITrackingAgent()
        variance_agent = VarianceExplanationAgent()
        scenario_agent = ScenarioModelingAgent()
        budget_agent = BudgetBuilderAgent()
        reporting_agent = ReportingAgent()
        initiative_agent = StrategicInitiativeAgent()

        # ------------------- FORECAST -------------------
        try:
            revenue, expense, capital = await asyncio.gather(
                revenue_agent.run(company_id, db),
                expense_agent.run(company_id, db),
                capital_agent.run(db)
            )
        except Exception as e:
            logger.exception(f"Error in forecasting agents: {e}")
            revenue, expense, capital = {}, {}, {}

        # ------------------- INITIATIVES -------------------
        try:
            initiatives = await initiative_agent.run(db)
        except Exception as e:
            logger.exception(f"Initiative error: {e}")
            initiatives = []

        # ------------------- SCENARIO -------------------
        last_revenue = revenue.get("forecast", [])[-1].get("yhat") if revenue.get("forecast") else 0
        last_expense = expense.get("forecast", [])[-1].get("yhat") if expense.get("forecast") else 0

        try:
            scenarios = await scenario_agent.run(last_revenue, last_expense)
        except Exception as e:
            logger.exception(f"Scenario error: {e}")
            scenarios = {}

        # Scenario → forecast adjustment
        if scenarios.get("scenarios"):
            base_case = scenarios["scenarios"].get("base", {})
            if base_case.get("revenue"):
                rev_factor = base_case["revenue"]["mean"] / last_revenue if last_revenue else 1
                for f in revenue.get("forecast", []):
                    f["yhat"] *= rev_factor
            if base_case.get("expense"):
                exp_factor = base_case["expense"]["mean"] / last_expense if last_expense else 1
                for f in expense.get("forecast", []):
                    f["yhat"] *= exp_factor

        # ------------------- BUDGET + KPI -------------------
        budget = await budget_agent.run(
            revenue.get("forecast", []),
            expense.get("forecast", [])
        )
        kpis = await kpi_agent.run(company_id, db)

        # ------------------- VARIANCE -------------------
        rows = (
            db.query(FinancialMetric)
            .filter(FinancialMetric.company_id == company_id)
            .order_by(FinancialMetric.period)
            .all()
        )

        if rows and revenue.get("forecast"):
            latest_actual = rows[-1].revenue or 0
            latest_forecast = revenue["forecast"][-1]["yhat"] if revenue.get("forecast") else 0

            variance = await variance_agent.run(latest_actual, latest_forecast)

            # Feedback loop
            if abs(variance.get("percentage", 0)) > settings.KPI_ALERT_THRESHOLD:
                revenue["forecast"] = await revenue_agent.adjust_forecast(
                    revenue["forecast"], variance
                )
        else:
            variance = {"variance": 0, "percentage": 0, "explanation": "Not enough data"}

        # ------------------- INSIGHTS -------------------
        last_budget = budget.get("budget", [])[-1] if budget.get("budget") else {"profit": 0}

        insight = f"""
Revenue variance is {variance.get('percentage')}%.
Revenue: {last_revenue}, Expense: {last_expense}.
Possible reason: change in growth or cost behavior.
"""

        # ------------------- PDF -------------------
        try:
            identifier = company_id if company_id else company_name
            pdf_file = await to_thread.run_sync(
                reporting_agent.generate_board_pack,
                f"board_pack_{identifier}_{int(asyncio.get_event_loop().time())}.pdf",
                db
            )
        except Exception as e:
            logger.exception(f"PDF error: {e}")
            pdf_file = None

        # ------------------- EMAIL -------------------
        # ------------------- EMAIL -------------------

        try:
    # 🔥 Safe defaults
             variance_pct = variance.get("percentage", 0) if isinstance(variance, dict) else 0
             kpi_list = kpis.get("kpis", []) if isinstance(kpis, dict) else []

    # 🔥 Decide whether to send email
             should_send = False

    # Trigger 1: High variance
             if abs(variance_pct) > settings.KPI_ALERT_THRESHOLD:
               should_send = True

    # Trigger 2: KPI alerts (red status)
             if any((k.get("status") == "red") for k in kpi_list if isinstance(k, dict)):
               should_send = True

    # 🔥 Send email only if conditions met
             if notify_email and pdf_file and should_send:
               template_loader = jinja2.FileSystemLoader("app/templates")
               template_env = jinja2.Environment(loader=template_loader)
               template = template_env.get_template("weekly_email.html")

               html_content = template.render(
            revenue=last_revenue,
            expense=last_expense,
            profit=last_budget.get("profit", 0) if isinstance(last_budget, dict) else 0,
            kpis=kpi_list,
            variance=variance.get("variance", 0) if isinstance(variance, dict) else 0,
            pdf_link=pdf_file
        )

               subject_name = company_id if company_id else company_name

               await send_email(
            subject=f"FP&A Alert - {subject_name}",
            html_content=html_content,
            to_email=notify_email,
            attachments=[pdf_file]
        )

        except Exception as e:
           logger.exception(f"Email error: {e}")

        # ------------------- RETURN -------------------
        return {
            "company_id": company_id,
            "company_name": company_name,
            "revenue": revenue,
            "expense": expense,
            "capital": capital,
            "initiatives": initiatives,
            "scenarios": scenarios,
            "budget": budget,
            "kpis": kpis,
            "variance": variance,
            "insight": insight,
            "report_pdf": pdf_file
        }
