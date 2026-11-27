import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db import get_db

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


@router.get("/health")
def health(db: Annotated[Session, Depends(get_db)]) -> JSONResponse:
    """Liveness + DB connectivity. Used by the Docker healthcheck."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        logger.warning("Health check: database unreachable")
        return JSONResponse(
            status_code=503, content={"detail": "Database unavailable", "database": "error"}
        )
    return JSONResponse(content={"status": "ok", "database": "ok"})
