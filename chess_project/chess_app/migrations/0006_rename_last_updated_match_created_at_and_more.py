# Generated by Django 5.1.2 on 2024-10-20 10:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chess_app', '0005_match'),
    ]

    operations = [
        migrations.RenameField(
            model_name='match',
            old_name='last_updated',
            new_name='created_at',
        ),
        migrations.AlterField(
            model_name='match',
            name='board_state',
            field=models.JSONField(default=dict),
        ),
    ]
