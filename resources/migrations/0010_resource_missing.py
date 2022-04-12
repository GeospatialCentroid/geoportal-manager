# Generated by Django 3.1.7 on 2022-04-01 23:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0009_auto_20220330_1620'),
    ]

    operations = [
        migrations.AddField(
            model_name='resource',
            name='missing',
            field=models.BooleanField(blank=True, help_text='Should the endpoint no longer list this resource', null=True),
        ),
    ]