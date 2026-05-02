from django.test import TestCase
from django.urls import reverse

from feed.models import Channel
from feed.services.rss_parsing import parse_xml_feed


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
    def test_parse_feed_extracts_video_fields(self):
        parsed_videos = parse_xml_feed(SAMPLE_FEED)

        self.assertEqual(len(parsed_videos), 2)
        self.assertEqual(parsed_videos[0].video_id, "test123")
        self.assertEqual(parsed_videos[0].thumbnail_url, "https://img.youtube.com/test.jpg")


class SubscriptionViewsTests(TestCase):
    def test_subscriptions_page_has_add_channel_link(self):
        response = self.client.get(reverse("subscriptions"))

        self.assertContains(response, reverse("subscriptions_create"))
        self.assertContains(response, "Add Channel")

    def test_subscriptions_create_persists_channel_with_defaults(self):
        response = self.client.post(
            reverse("subscriptions_create"),
            {"channel_id": "UC123"},
        )

        self.assertRedirects(response, reverse("subscriptions"))

        channel = Channel.objects.get(channel_id="UC123")
        self.assertEqual(channel.name, "Unknown")
        self.assertEqual(channel.upload_frequency, "biweekly")

    def test_subscriptions_create_requires_channel_id(self):
        response = self.client.post(reverse("subscriptions_create"), {"channel_id": ""})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Channel ID is required.")
        self.assertFalse(Channel.objects.filter(channel_id="").exists())
