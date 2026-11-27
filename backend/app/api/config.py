from fastapi import APIRouter
from pydantic import BaseModel

from app.api.auth import signup_open
from app.auth.deps import DbDep, SettingsDep

router = APIRouter(tags=["config"])


class ConfigResponse(BaseModel):
    app_name: str
    signup_open: bool


@router.get("/config")
def public_config(settings: SettingsDep, db: DbDep) -> ConfigResponse:
    """Public, non-secret config the frontend needs (single source for the app name)."""
    return ConfigResponse(
        app_name=settings.app_name, signup_open=signup_open(db, settings.allow_signup)
    )
