from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.config import Settings, get_settings

router = APIRouter(tags=["config"])


class ConfigResponse(BaseModel):
    app_name: str


@router.get("/config")
def public_config(settings: Annotated[Settings, Depends(get_settings)]) -> ConfigResponse:
    """Public, non-secret config the frontend needs (single source for the app name)."""
    return ConfigResponse(app_name=settings.app_name)
