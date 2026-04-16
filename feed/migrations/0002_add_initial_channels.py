from django.db import migrations


CHANNELS = [
    {
        "name": "Rachel & Jun's Adventures!",
        "channel_id": "UCSzHO_V894KyTDw3UgZS7gg",
    },
    {
        "name": "Two Minute Papers",
        "channel_id": "UCbfYPyITQ-7l4upoX8nvctg",
    },
    {
        "name": "SoundStills",
        "channel_id": "UCh69DAIH59RVe9SH2teWl5A",
    },
]


def seed_channels(apps, schema_editor):
    Channel = apps.get_model("feed", "Channel")

    for channel in CHANNELS:
        Channel.objects.update_or_create(
            channel_id=channel["channel_id"],
            defaults={
                "name": channel["name"],
                "upload_frequency": "biweekly",
            },
        )


def remove_channels(apps, schema_editor):
    Channel = apps.get_model("feed", "Channel")
    channel_ids = [channel["channel_id"] for channel in CHANNELS]
    Channel.objects.filter(channel_id__in=channel_ids).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("feed", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_channels, remove_channels),
    ]
