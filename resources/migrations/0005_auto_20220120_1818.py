# Generated by Django 3.1.7 on 2022-01-20 18:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0004_auto_20220120_1801'),
    ]

    operations = [
        migrations.AddField(
            model_name='url_type',
            name='_class',
            field=models.CharField(blank=True, help_text='When mapping, this field directs the web map to use a specific class.', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='url_type',
            name='_method',
            field=models.CharField(blank=True, help_text='The method for the class is defined here.', max_length=100, null=True),
        ),
    ]