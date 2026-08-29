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
    max_educational: Optional[int] = None
    min_educational: Optional[int] = None
    max_energy: Optional[int] = None
    min_energy: Optional[int] = None
    categories: Optional[list[str]] = []


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


class RuleUpdate(BaseModel):
    name: Optional[str] = None
    active_days: Optional[set[DayOfWeek]] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    max_educational: Optional[int] = None
    min_educational: Optional[int] = None
    max_energy: Optional[int] = None
    min_energy: Optional[int] = None
    categories: Optional[list[str]] = None


@router.patch("/rule/{rule_id}/")
def modify_rule(
    rule_id: str,
    payload: RuleUpdate,
    db: Session = Depends(get_db),
):
    changes = {}

    if payload.name:
        changes["name"] = payload.name
    if payload.active_days:
        changes["monday"] = DayOfWeek.MON in payload.active_days
        changes["tuesday"] = DayOfWeek.TUE in payload.active_days
        changes["wednesday"] = DayOfWeek.WED in payload.active_days
        changes["thursday"] = DayOfWeek.THU in payload.active_days
        changes["friday"] = DayOfWeek.FRI in payload.active_days
        changes["saturday"] = DayOfWeek.SAT in payload.active_days
        changes["sunday"] = DayOfWeek.SUN in payload.active_days
    if payload.start_time:
        changes["start_time"] = payload.start_time.replace(microsecond=0)
    if payload.end_time:
        changes["end_time"] = payload.end_time.replace(microsecond=0)
    if payload.max_educational:
        changes["max_educational"] = payload.max_educational
    if payload.min_educational:
        changes["min_educational"] = payload.min_educational
    if payload.max_energy:
        changes["max_energy"] = payload.max_energy
    if payload.min_energy:
        changes["min_energy"] = payload.min_energy
    if payload.categories:
        changes["category_tags"] = json.dumps(payload.categories)

    changes["updated_at"] = datetime.now()

    db.query(ScheduleRules).filter(ScheduleRules.id == rule_id).update(changes)
    db.commit()
    return {"success": True, "updated_at": changes["updated_at"]}


@router.delete("/rule/{rule_id}/")
def delete_rule(
    rule_id: str,
    db: Session = Depends(get_db),
):
    db.query(ScheduleRules).filter(ScheduleRules.id == rule_id).delete()
    db.commit()
    return {"success": True}
