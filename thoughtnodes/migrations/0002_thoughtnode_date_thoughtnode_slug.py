# Generated by Django 4.2.22 on 2025-06-07 18:38

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('thoughtnodes', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='thoughtnode',
            name='date',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='thoughtnode',
            name='slug',
            field=models.SlugField(auto_created=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
