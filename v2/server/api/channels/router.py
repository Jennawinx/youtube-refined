from dataclasses import asdict
import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session
from schema import Channels
from db import get_db
from model import CHANNEL_TYPE
from . import youtube

# Could potientially expand this beyond youtube

router = APIRouter(prefix="/youtube/channels", tags=["channels"])


def _formatChannel(channel: Channels) -> ChannelResponse:
    # Create new copy, do not mutate db entry via ORM
    new = {k: v for k, v in channel.__dict__.items()}
    new["category_tags"] = json.loads(channel.category_tags)
    return new


class ChannelResponse(BaseModel):
    channel_id: str
    name: str
    created_at: str
    category_tags: list[str]
    upload_frequency: str
    id: str
    updated_at: str
    last_updated: str


class GetChannelsResponse(BaseModel):
    channels: list[ChannelResponse]


@router.get("/")
def get_channels(
    db: Session = Depends(get_db),
    page_size: Optional[int] = 30,
    page: Optional[int] = 0,
    search: Optional[str] = "",
    categories: Optional[str] = "",
):
    _query = db.query(Channels)
    _search = search.strip()
    _categories = categories.split(",")

    if _search:
        _query = _query.filter(Channels.name.icontains(search))

    if _categories:
        conditions = []
        for tag in _categories:
            conditions.append(Channels.category_tags.icontains(tag.strip()))
        _query = _query.filter(or_(*conditions))

    results = _query.limit(page_size).offset(page * page_size).all()

    return {"channels": [_formatChannel(row) for row in results]}


class FindChannelResponse(BaseModel):
    channel_id: str
    name: str
    description: Optional[str]
    thumbnail_url: Optional[str]
    type: CHANNEL_TYPE


class FindChannelsResponse(BaseModel):
    channels: list[FindChannelResponse]


@router.post("/find")
def add_channel(
    search: str,
):
    results = []
    for channel in youtube.search_channels(search):
        results.append(
            # NOTES: apparently this is an anti-pattern O.O?
            FindChannelResponse(
                channel_id=channel.channel_id,
                name=channel.name,
                description=channel.description,
                thumbnail_url=channel.thumbnail_url,
                type=CHANNEL_TYPE.YOUTUBE,
            )
        )

    return {"channels": results}


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


@router.post("/refresh/{channel_id}")
def refresh_channels(
    channel_id: str,
    db: Session = Depends(get_db),
    page_size: Optional[int] = 30,
    page: Optional[int] = 0,
):
    # TODO:
    return {
        "channels": db.query(Channels).limit(page_size).offset(page * page_size).all()
    }


@router.delete("/{channel_id}")
def delete_channel(
    db: Session = Depends(get_db),
):
    # TODO:
    return {}
