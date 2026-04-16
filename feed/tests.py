from django.test import TestCase

from feed.services.rss import MIN_DURATION_SECONDS, ParsedVideo, parse_feed, should_skip_video


SAMPLE_FEED = b"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<feed xmlns:yt=\"http://www.youtube.com/xml/schemas/2015\" xmlns:media=\"http://search.yahoo.com/mrss/\" xmlns=\"http://www.w3.org/2005/Atom\">
	<entry>
		<id>yt:video:test123</id>
		<yt:videoId>test123</yt:videoId>
		<title>Sample Video</title>
		<link rel=\"alternate\" href=\"https://www.youtube.com/watch?v=test123\" />
		<published>2026-04-15T12:00:00+00:00</published>
		<media:group>
			<media:description>This is a regular upload.</media:description>
			<media:thumbnail url=\"https://img.youtube.com/test.jpg\" />
			<yt:duration seconds=\"245\" />
		</media:group>
	</entry>
	<entry>
		<id>yt:video:short456</id>
		<yt:videoId>short456</yt:videoId>
		<title>Short Clip</title>
		<link rel=\"alternate\" href=\"https://www.youtube.com/watch?v=short456\" />
		<published>2026-04-15T13:00:00+00:00</published>
		<media:group>
			<media:description>Watch this #Shorts upload</media:description>
			<yt:duration seconds=\"90\" />
		</media:group>
	</entry>
</feed>
"""


class RssServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.sample_publish_date = parse_feed(SAMPLE_FEED)[0].publish_date

    def test_parse_feed_extracts_video_fields(self):
        parsed_videos = parse_feed(SAMPLE_FEED)

        self.assertEqual(len(parsed_videos), 2)
        self.assertEqual(parsed_videos[0].video_id, "test123")
        self.assertEqual(parsed_videos[0].thumbnail_url, "https://img.youtube.com/test.jpg")
        self.assertEqual(parsed_videos[0].duration_seconds, 245)

    def test_should_skip_video_detects_shorts_marker_case_insensitively(self):
        parsed_video = ParsedVideo(
            video_id="abc",
            title="Title",
            description="new #ShOrTs clip",
            url="https://www.youtube.com/watch?v=abc",
            thumbnail_url="",
            publish_date=self.sample_publish_date,
            duration_seconds=MIN_DURATION_SECONDS,
        )

        self.assertTrue(should_skip_video(parsed_video))

    def test_should_skip_video_detects_short_duration(self):
        parsed_video = ParsedVideo(
            video_id="abc",
            title="Title",
            description="normal video",
            url="https://www.youtube.com/watch?v=abc",
            thumbnail_url="",
            publish_date=self.sample_publish_date,
            duration_seconds=MIN_DURATION_SECONDS - 1,
        )

        self.assertTrue(should_skip_video(parsed_video))

    def test_should_skip_video_allows_missing_duration_by_default(self):
        parsed_video = ParsedVideo(
            video_id="abc",
            title="Title",
            description="normal video",
            url="https://www.youtube.com/watch?v=abc",
            thumbnail_url="",
            publish_date=self.sample_publish_date,
            duration_seconds=None,
        )

        self.assertFalse(should_skip_video(parsed_video))

    def test_should_skip_video_blocks_missing_duration_in_strict_mode(self):
        parsed_video = ParsedVideo(
            video_id="abc",
            title="Title",
            description="normal video",
            url="https://www.youtube.com/watch?v=abc",
            thumbnail_url="",
            publish_date=self.sample_publish_date,
            duration_seconds=None,
        )

        self.assertTrue(should_skip_video(parsed_video, strict_duration=True))
