from collections import Counter
from django.db import migrations, models


def populate_channel_category_tags(apps, schema_editor):
    Channel = apps.get_model("feed", "Channel")
    Video = apps.get_model("feed", "Video")

    for channel in Channel.objects.all():
        tag_counts = Counter()
        for tags in Video.objects.filter(channel=channel).values_list("category_tags", flat=True):
            if tags:
                tag_counts.update(tags)
        channel.category_tags = [tag for tag, count in tag_counts.items() if count >= 3]
        channel.save(update_fields=["category_tags"])


class Migration(migrations.Migration):

    dependencies = [
        ("feed", "0005_remove_feedrule_category_tag_and_add_category_tags"),
    ]

    operations = [
        migrations.AddField(
            model_name="channel",
            name="category_tags",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.RunPython(populate_channel_category_tags, migrations.RunPython.noop),
    ]
