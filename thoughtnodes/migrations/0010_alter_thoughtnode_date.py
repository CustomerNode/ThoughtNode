# Generated by Django 4.2.22 on 2025-06-07 22:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('thoughtnodes', '0009_alter_thoughtnode_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='thoughtnode',
            name='date',
            field=models.DateTimeField(),
        ),
    ]
