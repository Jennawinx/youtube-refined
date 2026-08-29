from datetime import datetime, time
from enum import Enum
import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from schema import ScheduleRules
from db import get_db


class DayOfWeek(str, Enum):
    MON = "monday"
    TUE = "tuesday"
    WED = "wednesday"
    THU = "thursday"
    FRI = "friday"
    SAT = "saturday"
    SUN = "sunday"


router = APIRouter(prefix="/feed_schedule", tags=["feed_schedule"])


@router.get("/")
def get_schedule(
    db: Session = Depends(get_db),
):
    # TODO:
    return {}


@router.get("/rules")
def get_schedule(
    db: Session = Depends(get_db),
):
    return {
        "rules": db.query(ScheduleRules)
        .order_by(ScheduleRules.start_time.asc(), ScheduleRules.name.asc())
        .all()
    }


class RuleCreate(BaseModel):
    name: str
    active_days: set[DayOfWeek]
    start_time: time
    end_time: time
    max_educational: Optional[int]
    min_educational: Optional[int]
    max_energy: Optional[int]
    min_energy: Optional[int]
    categories: list[str]


@router.post("/rule")
def create_rule(
    payload: RuleCreate,
    db: Session = Depends(get_db),
):
    now = datetime.now()
    rule = ScheduleRules(
        name=payload.name,
        monday=DayOfWeek.MON in payload.active_days,
        tuesday=DayOfWeek.TUE in payload.active_days,
        wednesday=DayOfWeek.WED in payload.active_days,
        thursday=DayOfWeek.THU in payload.active_days,
        friday=DayOfWeek.FRI in payload.active_days,
        saturday=DayOfWeek.SAT in payload.active_days,
        sunday=DayOfWeek.SUN in payload.active_days,
        start_time=payload.start_time.replace(microsecond=0),
        end_time=payload.end_time.replace(microsecond=0),
        created_at=now,
        updated_at=now,
        max_educational=payload.max_educational,
        min_educational=payload.min_educational,
        max_energy=payload.max_energy,
        min_energy=payload.min_energy,
        category_tags=json.dumps(payload.categories),
    )
    db.add(rule)
    db.commit()
    return {"success": True}


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
