from datetime import datetime
from enum import Enum
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from schema import ScheduleRules
from db import get_db

router = APIRouter(prefix="/feed_schedule", tags=["feed_schedule"])

class DayOfWeek(str, Enum):
    MON = "monday"
    TUE = "tuesday"
    WED = "wednesday"
    THU = "thursday"
    FRI = "friday"
    SAT = "saturday"
    SUN = "sunday"


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
        "rules": db.query(ScheduleRules).order_by(
            ScheduleRules.start_time.asc, ScheduleRules.name.asc
        )
    }


@router.post("/rule")
def create_rule(
    db: Session = Depends(get_db),
    name=str,
    active_days=set[DayOfWeek],
    start_time=datetime,
    end_time=datetime,
    max_educational=Optional[int],
    min_educational=Optional[int],
    max_energy=Optional[int],
    min_energy=Optional[int],
    categories=list[str],
):
    now = datetime.now()

    ScheduleRules(
        name=name,
        monday=DayOfWeek.MON in active_days,
        tuesday=DayOfWeek.TUE in active_days,
        wednesday=DayOfWeek.WED in active_days,
        thursday=DayOfWeek.THU in active_days,
        friday=DayOfWeek.FRI in active_days,
        saturday=DayOfWeek.SAT in active_days,
        sunday=DayOfWeek.SUN in active_days,
        start_time=start_time,
        end_time=end_time,
        created_at=now,
        updated_at=now,
        max_educational=max_educational,
        min_educational=min_educational,
        max_energy=max_energy,
        min_energy=min_energy,
        category_tags=categories
    )

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
