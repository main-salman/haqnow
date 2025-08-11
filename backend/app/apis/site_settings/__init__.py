from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
import json
import structlog

from app.auth.user import AdminUser
from app.database import get_db, SiteSetting

logger = structlog.get_logger()

router = APIRouter()


class AnnouncementPayload(BaseModel):
    enabled: bool
    content: str  # plain text or HTML snippet


SETTING_KEY = "announcement_banner"


@router.get("/announcement", response_model=AnnouncementPayload)
async def get_announcement(db: Session = Depends(get_db)):
    try:
        setting = db.query(SiteSetting).filter(SiteSetting.key == SETTING_KEY).first()
        if not setting:
            # Initial default announcement
            return AnnouncementPayload(enabled=True, content="Launching September 2025")
        try:
            data = json.loads(setting.value)
        except Exception:
            data = {"enabled": False, "content": ""}
        return AnnouncementPayload(enabled=bool(data.get("enabled")), content=str(data.get("content") or ""))
    except Exception as e:
        logger.error("Failed to get announcement", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get announcement")


@router.put("/announcement", response_model=AnnouncementPayload)
async def upsert_announcement(
    payload: AnnouncementPayload,
    admin_user: AdminUser,
    db: Session = Depends(get_db),
):
    try:
        setting = db.query(SiteSetting).filter(SiteSetting.key == SETTING_KEY).first()
        value = json.dumps({"enabled": payload.enabled, "content": payload.content})
        if setting:
            setting.value = value
            setting.updated_by = getattr(admin_user, "email", None) or getattr(admin_user, "sub", None)
        else:
            setting = SiteSetting(
                key=SETTING_KEY,
                value=value,
                updated_by=getattr(admin_user, "email", None) or getattr(admin_user, "sub", None),
            )
            db.add(setting)
        db.commit()
        db.refresh(setting)
        return AnnouncementPayload(**json.loads(setting.value))
    except Exception as e:
        db.rollback()
        logger.error("Failed to update announcement", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update announcement")


