# Generated by Django 4.2.9 on 2024-10-31 01:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('artwork', '0006_question_answer'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='question',
            name='author',
        ),
        migrations.RemoveField(
            model_name='question',
            name='post',
        ),
        migrations.DeleteModel(
            name='Answer',
        ),
        migrations.DeleteModel(
            name='Question',
        ),
    ]
