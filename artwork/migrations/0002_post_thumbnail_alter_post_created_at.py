# Generated by Django 4.2.9 on 2024-10-20 02:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("artwork", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="post",
            name="thumbnail",
            field=models.ImageField(
                blank=True, null=True, upload_to="post_thumbnails/"
            ),
        ),
        migrations.AlterField(
            model_name="post",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
