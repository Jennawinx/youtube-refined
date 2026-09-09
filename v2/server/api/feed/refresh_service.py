import json

from logger import logger
from datetime import datetime
from fastapi import Depends

from clients.youtube import YouTubeVideo
from clients.video_categorizer import VideoCategorizer, VideoDetails
from clients.channel_categorizer import ChannelCategorizer
from db import get_db
from schema import Videos, Channels

class RefreshService:

    def __init__(
        self,
        db=Depends(get_db),
        videoCategorizer: VideoCategorizer = Depends(),
        channelCategorizer: ChannelCategorizer = Depends(),
    ):
        self._db = db
        self._videoCategorizer = videoCategorizer
        self._channelCategorizer = channelCategorizer

    # TODO: WIP
    def update_video_list(self, channel_id, videos: list[YouTubeVideo]) -> int:

        db = self._db
        channel = db.query(Channels).filter(Channels.channel_id == channel_id).first()

        if not channel:
            logger.error("Cannot update video list for channel {channel_id}")

        # Filter out shorts
        video_ids = {v.video_id for v in videos}
        existing_video_ids = set(
            db.query(Videos).filter(Videos.video_id.in_(video_ids)).all()
        )
        new_videos = [v for v in videos if v.video_id not in existing_video_ids]
        
        # Categorize the videos
        categorized_videos = self._videoCategorizer.categorize_videos_advanced(
            [
                VideoDetails(
                    id=v.video_id, thumbnail_url=v.thumbnail_url_low_res, title=v.title
                )
                for v in new_videos
            ]
        )

        logger.info(f"Found {len(new_videos)} new videos for channel {channel.name}")
        now = datetime.now()

        for i in range(len(new_videos)):
            video_info = new_videos[i]
            category_info = categorized_videos[i]
            new_video = Videos(
                channel_id=channel.id,
                title=video_info.title,
                description=video_info.description,
                url=video_info.url,
                thumbnail_url=video_info.thumbnail_url,
                publish_date=video_info.publish_date,
                presentation=category_info.presentation,
                category_tags=json.dumps(category_info.topics),
                energy=category_info.energy,
                educational=category_info.educational,
                is_watched=False,
                video_id=video_info.video_id,
                created_at=now,
                updated_at=now,
            )
            db.add(new_video)

        channel.last_updated = datetime.now()
        db.flush()

        return len(new_videos)
