from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.security import ROLE_PERMISSIONS, get_current_user

router = APIRouter(prefix="/auth", tags=["auth-rbac"])


class DemoTokenRequest(BaseModel):
    user_id: str = "demo-user"
    role: str = "Admin"


@router.post("/token")
def token(payload: DemoTokenRequest):
    role = payload.role if payload.role in ROLE_PERMISSIONS else "Viewer"
    return {
        "access_token": f"demo-oauth-token-{payload.user_id}-{role}",
        "token_type": "bearer",
        "user_id": payload.user_id,
        "role": role,
        "permissions": sorted(ROLE_PERMISSIONS[role]),
    }


@router.get("/me")
def me(user: dict = Depends(get_current_user)):
    return user


@router.get("/roles")
def roles():
    return [{"role": role, "permissions": sorted(permissions)} for role, permissions in ROLE_PERMISSIONS.items()]
