# Generated by Django 3.1.7 on 2022-04-15 21:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0012_auto_20220407_1855'),
    ]

    operations = [
        migrations.AlterField(
            model_name='georeference_request',
            name='name',
            field=models.CharField(blank=True, max_length=400, null=True),
        ),
    ]