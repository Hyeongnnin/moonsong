from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("documents", "0002_alter_generateddocument_template"),
    ]

    operations = [
        migrations.AddField(
            model_name="generateddocument",
            name="title",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
    ]
