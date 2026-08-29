from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from schema import Channels
from db import get_db


# Could potientially expand this beyond youtube

router = APIRouter(prefix="/youtube/channels", tags=["channels"])


@router.get("/")
def get_channels(
    db: Session = Depends(get_db),
    page_size: Optional[int] = 30,
    page: Optional[int] = 0,
):
    # TODO:
    return {
        "channels": db.query(Channels).limit(page_size).offset(page * page_size).all()
    }


@router.get("/search")
def search_channels(
    db: Session = Depends(get_db),
    page_size: Optional[int] = 30,
    page: Optional[int] = 0,
):
    # TODO:
    return {
        "channels": db.query(Channels).limit(page_size).offset(page * page_size).all()
    }


@router.get("/refresh")
def refresh_channels(
    db: Session = Depends(get_db),
    page_size: Optional[int] = 30,
    page: Optional[int] = 0,
):
    # TODO:
    return {
        "channels": db.query(Channels).limit(page_size).offset(page * page_size).all()
    }


@router.post("/add")
def add_channel(
    db: Session = Depends(get_db),
):
    # TODO:
    return {}


@router.patch("/{channel_id}")
def edit_channel(
    db: Session = Depends(get_db),
):
    # TODO:
    return {}


@router.delete("/{channel_id}")
def delete_channel(
    db: Session = Depends(get_db),
):
    # TODO:
    return {}
