from django.db import migrations, models


def migrate_category_tag_to_tags(apps, schema_editor):
    FeedRule = apps.get_model("feed", "FeedRule")
    for rule in FeedRule.objects.all().iterator():
        raw_tag = (rule.category_tag or "").strip()
        rule.category_tags = [raw_tag] if raw_tag else []
        rule.save(update_fields=["category_tags"])


class Migration(migrations.Migration):

    dependencies = [
        ("feed", "0004_feedrule_max_educational_feedrule_max_energy_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="feedrule",
            name="category_tags",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.RunPython(migrate_category_tag_to_tags, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="feedrule",
            name="category_tag",
        ),
    ]
