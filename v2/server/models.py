from typing import Optional
import datetime

from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, Time
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass


class FeedChannel(Base):
    __tablename__ = 'feed_channel'
    __table_args__ = (
        CheckConstraint('(JSON_VALID("category_tags") OR "category_tags" IS NULL)'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    channel_id: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    upload_frequency: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    category_tags: Mapped[str] = mapped_column(Text, nullable=False)
    last_updated: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)

    feed_video: Mapped[list['FeedVideo']] = relationship('FeedVideo', back_populates='channel')


class FeedScheduleRule(Base):
    __tablename__ = 'feed_schedule_rule'
    __table_args__ = (
        CheckConstraint('"max_educational" >= 0'),
        CheckConstraint('"max_energy" >= 0'),
        CheckConstraint('"min_educational" >= 0'),
        CheckConstraint('"min_energy" >= 0'),
        CheckConstraint('(JSON_VALID("category_tags") OR "category_tags" IS NULL)')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    monday: Mapped[bool] = mapped_column(Boolean, nullable=False)
    tuesday: Mapped[bool] = mapped_column(Boolean, nullable=False)
    wednesday: Mapped[bool] = mapped_column(Boolean, nullable=False)
    thursday: Mapped[bool] = mapped_column(Boolean, nullable=False)
    friday: Mapped[bool] = mapped_column(Boolean, nullable=False)
    saturday: Mapped[bool] = mapped_column(Boolean, nullable=False)
    sunday: Mapped[bool] = mapped_column(Boolean, nullable=False)
    start_time: Mapped[datetime.time] = mapped_column(Time, nullable=False)
    end_time: Mapped[datetime.time] = mapped_column(Time, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    category_tags: Mapped[str] = mapped_column(Text, nullable=False)
    max_educational: Mapped[Optional[int]] = mapped_column(Integer)
    max_energy: Mapped[Optional[int]] = mapped_column(Integer)
    min_educational: Mapped[Optional[int]] = mapped_column(Integer)
    min_energy: Mapped[Optional[int]] = mapped_column(Integer)


class FeedVideo(Base):
    __tablename__ = 'feed_video'
    __table_args__ = (
        CheckConstraint('(JSON_VALID("category_tags") OR "category_tags" IS NULL)'),
        Index('feed_video_channel_id_4743eefc', 'channel_id')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    video_id: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(String(200), nullable=False)
    thumbnail_url: Mapped[str] = mapped_column(String(200), nullable=False)
    publish_date: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    category_tags: Mapped[str] = mapped_column(Text, nullable=False)
    energy: Mapped[int] = mapped_column(Integer, nullable=False)
    educational: Mapped[int] = mapped_column(Integer, nullable=False)
    is_watched: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    channel_id: Mapped[int] = mapped_column(ForeignKey('feed_channel.id'), nullable=False)
    presentation: Mapped[str] = mapped_column(String(255), nullable=False)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer)

    channel: Mapped['FeedChannel'] = relationship('FeedChannel', back_populates='feed_video')
