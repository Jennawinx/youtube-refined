from django.core.management.base import BaseCommand

from feed.services.rss import refresh_all_channels


class Command(BaseCommand):
    help = "Fetch recent videos from YouTube RSS feeds for all seeded channels."

    def add_arguments(self, parser):
        parser.add_argument(
            "--strict-duration",
            action="store_true",
            help="Skip videos when duration metadata is unavailable.",
        )

    def handle(self, *args, **options):
        strict_duration = options["strict_duration"]
        stats_list = refresh_all_channels(strict_duration=strict_duration)

        total_created = 0
        total_existing = 0
        total_skipped = 0

        for stats in stats_list:
            total_created += stats.created
            total_existing += stats.existing
            total_skipped += stats.skipped
            self.stdout.write(
                f"{stats.channel_name}: fetched={stats.fetched} created={stats.created} "
                f"existing={stats.existing} skipped={stats.skipped}"
            )

        self.stdout.write(self.style.SUCCESS("RSS refresh complete."))
        self.stdout.write(
            f"Totals: created={total_created} existing={total_existing} "
            f"skipped={total_skipped}"
        )
