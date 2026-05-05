from fastapi import Header
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)

ROLE_PERMISSIONS = {
    "Viewer": {"read_dashboards", "get_company_financials", "get_kpi_risks"},
    "Finance Analyst": {"read_dashboards", "run_forecasts", "run_scenarios", "sync_data"},
    "CFO": {"read_dashboards", "run_forecasts", "run_scenarios", "approve_recommendations", "generate_reports"},
    "Admin": {"read_dashboards", "run_forecasts", "run_scenarios", "approve_recommendations", "generate_reports", "admin_tools"},
}


def get_current_user(
    authorization: str | None = Header(default=None),
    x_user_role: str = Header(default="Admin"),
    x_user_id: str = Header(default="demo-user"),
) -> dict:
    token = authorization.replace("Bearer ", "") if authorization else "demo-token"
    role = x_user_role if x_user_role in ROLE_PERMISSIONS else "Viewer"
    return {
        "user_id": x_user_id,
        "role": role,
        "token_type": "Bearer",
        "authenticated": bool(token),
        "permissions": sorted(ROLE_PERMISSIONS[role]),
    }
