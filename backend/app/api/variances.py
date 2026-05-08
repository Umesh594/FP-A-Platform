from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.dependencies import get_db
from datetime import date
from app.models.financials import FinancialMetric

router = APIRouter(prefix="/variances", tags=["variances"])


@router.get("/{company_id}/{period}")
async def get_variances(company_id: int, period: str, db: Session = Depends(get_db)):
    """
    Fetch variance explanation for a specific company and period.
    Pulls actual & forecast directly from DB.
    """
    try:
        if len(period) == 7:
            period = f"{period}-01"
        period_date = date.fromisoformat(period)
        metric: FinancialMetric = db.query(FinancialMetric).filter(
            FinancialMetric.company_id == company_id,
            FinancialMetric.period == period_date
        ).first()

        if not metric:
            raise HTTPException(status_code=404, detail="No financial metric found for this period")

        # Use RevenueForecastAgent to fetch accurate forecast
        from app.agents.revenue_agent import RevenueForecastAgent
        revenue_agent = RevenueForecastAgent()
        forecast_result = await revenue_agent.run(company_id, db)
        forecast_list = forecast_result.get("forecast", [])
        forecast_value = forecast_list[-1].get("yhat") if forecast_list else metric.revenue

        from app.agents.variance_agent import VarianceExplanationAgent

        variance_agent = VarianceExplanationAgent()
        return await variance_agent.run(actual=metric.revenue, forecast=forecast_value)

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format, use YYYY-MM or YYYY-MM-DD")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
