from enum import Enum
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from schema import Videos
from db import get_db


class FeedMode(str, Enum):
    RECOMMENDED = "recommend"
    ALL = "all"
    CUSTOM = "custom"


router = APIRouter(prefix="/feed", tags=["feed"])


@router.get("/")
def get_feed(
    db: Session = Depends(get_db),
    page_size: Optional[int] = 30,
    page: Optional[int] = 0,
    mode: Optional[FeedMode] = FeedMode.RECOMMENDED,
):
    # TODO:
    return {
        "videos": db.query(Videos)
        .order_by(Videos.created_at.desc())
        .offset(page * page_size)
        .limit(page_size)
        .all()
    }


@router.get("/refresh")
def refresh_feed(
    db: Session = Depends(get_db),
    page_size: Optional[int] = 30,
    page: Optional[int] = 0,
):
    # TODO:
    return {
        "videos": db.query(Videos)
        .order_by(Videos.created_at.desc())
        .offset(page * page_size)
        .limit(page_size)
        .all()
    }


@router.patch("/video/{video_id}/watched")
def video_watched(
    video_id: str,
    db: Session = Depends(get_db),
):
    success = (
        db.query(Videos).filter(Videos.id == video_id).update({"is_watched": True})
    ) > 0

    db.commit()

    return {"success": success}
