from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ReelJob",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("processing", "Processing"),
                            ("done", "Done"),
                            ("error", "Error"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("source_url", models.URLField(blank=True)),
                ("video_file", models.FileField(upload_to="reels/videos/%Y/%m/%d/")),
                ("result_city", models.CharField(blank=True, max_length=128)),
                ("result_country", models.CharField(blank=True, max_length=128)),
                ("confidence", models.FloatField(blank=True, null=True)),
                ("reasoning", models.TextField(blank=True)),
                ("audio_transcript", models.TextField(blank=True)),
                ("raw_response", models.TextField(blank=True)),
                ("error_message", models.TextField(blank=True)),
                ("frames_meta", models.JSONField(blank=True, default=list)),
            ],
        ),
    ]
