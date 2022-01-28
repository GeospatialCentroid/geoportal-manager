# Generated by Django 3.1.7 on 2022-01-20 18:44

from django.db import migrations
import json

from pathlib import Path


DATA_FILENAME = 'url_ref.json'
def load_data(apps, schema_editor):
    URL_Type = apps.get_model('resources', 'URL_Type')

    # access file level one above current
    jsonfile = Path(__file__).parents[1] / DATA_FILENAME

    with open(str(jsonfile)) as datafile:
        objects = json.load(datafile)
        # we're going to populate the table in 3 steps

        # 1) generate the categories
        for obj in objects:
            {"name": "imageserver", "service": "true", "ref": "urn:x-esri:serviceType:ArcGIS#ImageMapLayer",
             "class": "esri", "method": "imageMapLayer"},
            if 'service' not in obj:
                obj['service']=False
            else :
                obj['service'] = True

            if 'class' not in obj:
                obj['class']=""
            if 'method' not in obj:
                obj['method'] = ""

            URL_Type(name=obj['name'], ref = obj['ref'],service=obj['service'],_class=obj['class'],_method=obj['method']).save()



def reverse_func(apps, schema_editor):
    # forwards_func() creates two Country instances,
    # so reverse_func() should delete them.
    # todo empty the database tables
    print("Reversed!")

class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0005_auto_20220120_1818'),
    ]

    operations = [
        migrations.RunPython(load_data, reverse_func)
    ]
