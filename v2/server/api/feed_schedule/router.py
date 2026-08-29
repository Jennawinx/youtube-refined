from enum import Enum
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import Videos
from db import get_db

router = APIRouter(prefix="/feed_schedule", tags=["feed_schedule"])

@router.get("/")
def get_schedule(
    db: Session = Depends(get_db),
):
    # TODO:
    return {}


@router.post("/rule")
def create_rule(
    db: Session = Depends(get_db),
):
    # TODO:
    return {}


@router.patch("/rule/{rule_id}/")
def modify_rule(
    rule_id: str,
    db: Session = Depends(get_db),
):
    # TODO:
    return {}


@router.delete("/rule/{rule_id}/")
def delete_rule(
    rule_id: str,
    db: Session = Depends(get_db),
):
    # TODO:
    return {}
