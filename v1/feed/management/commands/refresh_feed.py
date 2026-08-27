from django.core.management.base import BaseCommand
from feed.services.rss import refresh_all_channels

class Command(BaseCommand):
    help = "Fetch recent videos from YouTube RSS feeds for all seeded channels."

    # def add_arguments(self, parser):
    #     parser.add_argument(
    #         "--strict-duration",
    #         action="store_true",
    #         help="Skip videos when duration metadata is unavailable.",
    #     )

    def handle(self, *args, **options):
        stats_list = refresh_all_channels()
        total_created = 0

        for stats in stats_list:
            total_created += stats
            self.stdout.write(
                f"{stats.channel_name}: fetched={stats.fetched} created={stats.created} "
                f"existing={stats.existing} skipped={stats.skipped}"
            )

        self.stdout.write(self.style.SUCCESS("RSS refresh complete."))
        self.stdout.write(f"Totals: created={total_created}")
