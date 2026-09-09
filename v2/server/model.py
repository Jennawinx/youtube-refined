from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


def get_now() -> datetime:
    return datetime.now()


class SuccessAction(BaseModel):
    success: bool = True
    updated_at: datetime = Field(default_factory=get_now)


class DAY_OF_WEEK(str, Enum):
    MON = "monday"
    TUE = "tuesday"
    WED = "wednesday"
    THU = "thursday"
    FRI = "friday"
    SAT = "saturday"
    SUN = "sunday"


class CHANNEL_TYPE(str, Enum):
    YOUTUBE = "youtube"


DAY_NAMES = [
    DAY_OF_WEEK.MON,
    DAY_OF_WEEK.TUE,
    DAY_OF_WEEK.WED,
    DAY_OF_WEEK.THU,
    DAY_OF_WEEK.FRI,
    DAY_OF_WEEK.SAT,
    DAY_OF_WEEK.SUN,
]

COMMON_TOPICS = [
    "Actors",
    "AI and Machine Learning",
    "Animation",
    "Anime and Manga",
    "Art",
    "ASMR",
    "Beauty",
    "Biography",
    "Building",
    "Business",
    "Cafe",
    "Cooking",
    "Celebrity",
    "Culture",
    "Craft",
    "Day in the life",
    "Decor",
    "DIY",
    "Economics",
    "Economy",
    "Educational",
    "Finance and Investing",
    "Fitness",
    "Food",
    "Game",
    "Health",
    "Innovation",
    "Interior Design",
    "Kpop",
    "Language",
    "Living",
    "Math",
    "Mental Health",
    "Morning Routine",
    "Motivation",
    "Movie and TV",
    "Music",
    "Nature",
    "News",
    "Parenting",
    "Pets",
    "Politics",
    "Product Review",
    "Psychology",
    "Relaxation",
    "Science",
    "Shopping",
    "Software Development",
    "Sports",
    "Technology",
    "Travel",
]

PRESENTATION = ["Vlog", "Music", "Podcast", "Commentary", "Talk show", "Info"]
