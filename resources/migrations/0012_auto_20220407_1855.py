# Generated by Django 3.1.7 on 2022-04-07 18:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0011_auto_20220407_1636'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resource',
            name='parent',
            field=models.ManyToManyField(blank=True, related_name='parent_resource', to='resources.Resource'),
        ),
    ]
