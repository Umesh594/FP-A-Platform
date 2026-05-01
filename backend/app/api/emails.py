from fastapi import APIRouter
from pydantic import BaseModel
from app.services.email_service import send_email
from datetime import datetime, timezone

router = APIRouter(prefix="/emails", tags=["emails"])

EMAIL_TEMPLATES = [
    {
        "id": "weekly-summary",
        "name": "Weekly Portfolio Summary",
        "subject": "Summit Growth Weekly Portfolio Summary",
        "type": "summary",
        "recipients": ["partners@summitgrowth.com"],
        "status": "active",
    },
    {
        "id": "kpi-alert",
        "name": "KPI Threshold Alert",
        "subject": "FP&A Alert: KPI threshold breached",
        "type": "alert",
        "recipients": ["risk@summitgrowth.com", "partners@summitgrowth.com"],
        "status": "active",
    },
    {
        "id": "board-pack-ready",
        "name": "Board Pack Ready",
        "subject": "Monthly Board Pack is ready",
        "type": "report",
        "recipients": ["board@summitgrowth.com"],
        "status": "active",
    },
]

SEND_LOGS = []

class EmailPayload(BaseModel):
    to_email: str
    subject: str
    html_content: str


@router.get("/templates")
def get_email_templates():
    return EMAIL_TEMPLATES


@router.get("/logs")
def get_email_logs():
    return SEND_LOGS


@router.post("/send")
async def send_email_route(payload: EmailPayload):
    await send_email(
        subject=payload.subject,
        html_content=payload.html_content,
        to_email=payload.to_email,
        attachments=[]
    )
    SEND_LOGS.insert(0, {
        "id": f"log-{int(datetime.now(timezone.utc).timestamp() * 1000)}",
        "templateId": "manual",
        "templateName": payload.subject,
        "sentAt": datetime.now(timezone.utc).isoformat(),
        "recipients": [payload.to_email],
        "status": "delivered",
        "agentName": "Email Service",
    })
    return {"status": "sent"}
