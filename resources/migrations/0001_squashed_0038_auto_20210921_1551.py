# Generated by Django 3.1.7 on 2021-11-03 20:20

import ckeditor.fields
import datetime
import django.contrib.gis.db.models.fields
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


# Functions from the following migrations need manual copying.
# Move them and any dependencies into this file, then update the
# RunPython operations to refer to the local versions:
# resources.migrations.0003_auto_20210329_2048
# resources.migrations.0005_auto_20210329_2246

class Migration(migrations.Migration):

    replaces = [('resources', '0001_initial'), ('resources', '0002_auto_20210329_1956'), ('resources', '0003_auto_20210329_2048'), ('resources', '0004_auto_20210329_2243'), ('resources', '0005_auto_20210329_2246'), ('resources', '0006_auto_20210329_2303'), ('resources', '0007_end_point_end_point_type'), ('resources', '0008_auto_20210331_2215'), ('resources', '0009_resource_access_information'), ('resources', '0010_end_point_publisher'), ('resources', '0011_auto_20210401_0036'), ('resources', '0012_auto_20210401_1651'), ('resources', '0013_auto_20210401_2238'), ('resources', '0014_auto_20210401_2252'), ('resources', '0015_auto_20210403_0042'), ('resources', '0016_auto_20210505_1556'), ('resources', '0017_auto_20210506_1449'), ('resources', '0018_auto_20210513_0209'), ('resources', '0019_auto_20210513_0249'), ('resources', '0020_auto_20210520_0329'), ('resources', '0021_auto_20210522_1716'), ('resources', '0022_auto_20210523_1447'), ('resources', '0023_auto_20210524_1440'), ('resources', '0024_auto_20210530_2314'), ('resources', '0025_url_url_label'), ('resources', '0026_auto_20210623_1538'), ('resources', '0027_auto_20210623_1804'), ('resources', '0028_auto_20210803_2245'), ('resources', '0029_auto_20210806_2057'), ('resources', '0030_auto_20210818_1949'), ('resources', '0031_auto_20210825_0012'), ('resources', '0032_auto_20210826_2311'), ('resources', '0033_owner_full_name'), ('resources', '0034_auto_20210830_2304'), ('resources', '0035_auto_20210831_2234'), ('resources', '0036_auto_20210831_2303'), ('resources', '0037_community_input_georeference_request'), ('resources', '0038_auto_20210921_1551')]

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('code', models.CharField(max_length=4)),
                ('title', models.CharField(max_length=100)),
                ('desc', models.CharField(max_length=500)),
            ],
        ),
        migrations.CreateModel(
            name='End_Point',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('org_name', models.CharField(max_length=100)),
                ('url', models.CharField(max_length=512)),
            ],
        ),
        migrations.CreateModel(
            name='Harvest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(blank=True, null=True, verbose_name='Date harvested')),
                ('trigger_type', models.CharField(choices=[('s', 'schedule'), ('u', 'user')], max_length=1)),
            ],
        ),
        migrations.CreateModel(
            name='Language',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Place',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Publisher',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Type',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='URL_Type',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Resource',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('resource_id', models.CharField(max_length=100)),
                ('title', models.CharField(max_length=200)),
                ('bounding_box', django.contrib.gis.db.models.fields.PolygonField(srid=4326)),
                ('accessioned', models.DateTimeField(blank=True, null=True, verbose_name='Date accessioned')),
                ('alt_title', models.CharField(blank=True, max_length=100, null=True)),
                ('children', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='resource', to='resources.resource')),
                ('created', models.DateTimeField(blank=True, null=True, verbose_name='Date created')),
                ('description', models.TextField(blank=True, null=True)),
                ('layer_json', models.JSONField(blank=True, null=True)),
                ('license_info', models.TextField(blank=True, null=True)),
                ('modified', models.DateTimeField(blank=True, null=True, verbose_name='Date modified')),
                ('owner', models.CharField(blank=True, max_length=100)),
                ('raw_json', models.JSONField(blank=True, null=True)),
                ('thumbnail', models.CharField(blank=True, max_length=512, null=True)),
                ('year', models.IntegerField(blank=True, null=True, validators=[django.core.validators.MaxValueValidator(9999)])),
                ('category', models.ManyToManyField(blank=True, to='resources.Category')),
                ('end_point', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='resources.end_point')),
                ('harvest', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='resources.harvest')),
                ('languages', models.ManyToManyField(blank=True, to='resources.Language')),
                ('place', models.ManyToManyField(blank=True, to='resources.Place')),
                ('publisher', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='resources.publisher')),
                ('tag', models.ManyToManyField(blank=True, to='resources.Tag')),
                ('type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='resources.type')),
            ],
            options={
                'unique_together': {('resource_id', 'end_point')},
            },
        ),
        migrations.CreateModel(
            name='urls',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.CharField(max_length=512)),
                ('resource', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='resources.resource')),
                ('url_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='resources.url_type')),
            ],
        ),
        migrations.CreateModel(
            name='Change_Log',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('field_name', models.CharField(max_length=100)),
                ('date', models.DateTimeField(verbose_name='Date changed')),
                ('change_type', models.CharField(choices=[('o', 'origin'), ('a', 'automation'), ('u', 'user')], max_length=1)),
                ('resource', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='resources.resource')),
            ],
        ),
        migrations.CreateModel(
            name='Category_Keywords',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('category', models.ManyToManyField(to='resources.Category')),
            ],
        ),
        # migrations.RunPython(
        #     code=resources.migrations.0003_auto_20210329_2048.load_data,
        #     reverse_code=resources.migrations.0003_auto_20210329_2048.reverse_func,
        # ),
        migrations.AddField(
            model_name='place',
            name='name_lsad',
            field=models.CharField(default='', max_length=100),
        ),
        migrations.AddField(
            model_name='place',
            name='place_fp',
            field=models.CharField(default='', max_length=100),
        ),
        migrations.AddField(
            model_name='place',
            name='tate_fp',
            field=models.CharField(default='', max_length=100),
        ),
        migrations.AlterField(
            model_name='place',
            name='name',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterUniqueTogether(
            name='place',
            unique_together={('name', 'name_lsad')},
        ),
        # migrations.RunPython(
        #     code=resources.migrations.0005_auto_20210329_2246.load_data,
        #     reverse_code=resources.migrations.0005_auto_20210329_2246.reverse_func,
        # ),
        migrations.RenameField(
            model_name='place',
            old_name='tate_fp',
            new_name='state_fp',
        ),
        migrations.CreateModel(
            name='Owner',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('full_name', models.CharField(blank=True, max_length=150, null=True)),
            ],
        ),
        migrations.AlterField(
            model_name='resource',
            name='alt_title',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.RemoveField(
            model_name='resource',
            name='owner',
        ),
        migrations.AddField(
            model_name='end_point',
            name='publisher',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='resources.publisher'),
        ),
        migrations.AddField(
            model_name='resource',
            name='access_information',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterUniqueTogether(
            name='urls',
            unique_together={('url', 'url_type', 'resource')},
        ),
        migrations.RenameModel(
            old_name='urls',
            new_name='URL',
        ),
        migrations.RenameField(
            model_name='resource',
            old_name='children',
            new_name='parent',
        ),
        migrations.AlterField(
            model_name='resource',
            name='description',
            field=ckeditor.fields.RichTextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='resource',
            name='license_info',
            field=ckeditor.fields.RichTextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='resource',
            name='status_type',
            field=models.CharField(choices=[('as', 'Approved for Staging'), ('is', 'In Staging'), ('ap', 'Approved for Production'), ('ip', 'In Production'), ('nr', 'Needs Review'), ('rs', 'Remove from Staging'), ('rp', 'Remove from Production')], default='nr', max_length=2),
        ),
        migrations.CreateModel(
            name='Status_Log',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(blank=True, default=datetime.datetime.now, verbose_name='Date changed')),
                ('status_desc', models.CharField(max_length=200)),
                ('notes', models.TextField(blank=True, null=True)),
                ('resource', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='resources.resource')),
            ],
        ),
        migrations.CreateModel(
            name='Format',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
            ],
        ),
        migrations.AddField(
            model_name='resource',
            name='format',
            field=models.ForeignKey(blank=True, help_text='The format of the data. E.g Shapefile, GeoTIFF, JPEG, TIFF, ArcGRID, Paper Map, Geodatabase, JPEG, E00 Cartographic Material, ESRI Geodatabase, SQLite Database, GeoJSON, Raster Dataset, Scanned Map, etc. Used in Facet search', null=True, on_delete=django.db.models.deletion.SET_NULL, to='resources.format'),
        ),
        migrations.CreateModel(
            name='Geometry_Type',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
            ],
        ),
        migrations.AddField(
            model_name='resource',
            name='geometry_type',
            field=models.ForeignKey(blank=True, help_text='To differentiate between vector (Point, Line, Polygon), raster (Raster, Image), and nonspatial formats (table), or a combination (Mixed). Used as icon within interface', null=True, on_delete=django.db.models.deletion.SET_NULL, to='resources.geometry_type'),
        ),
        migrations.AlterField(
            model_name='resource',
            name='bounding_box',
            field=django.contrib.gis.db.models.fields.PolygonField(blank=True, null=True, srid=4326),
        ),
        migrations.AlterField(
            model_name='resource',
            name='id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
        migrations.AddField(
            model_name='end_point',
            name='end_point_type',
            field=models.CharField(choices=[('d', 'dcat'), ('a', 'arc_gis_rest'), ('c', 'CONTENTdm'), ('ds', 'dspace')], default='a', max_length=2),
        ),
        migrations.CreateModel(
            name='URL_Label',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.AddField(
            model_name='url',
            name='url_label',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='resources.url_label'),
        ),
        migrations.AlterField(
            model_name='resource',
            name='parent',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='resource', to='resources.resource'),
        ),
        migrations.AddField(
            model_name='resource',
            name='temporal_coverage',
            field=models.CharField(blank=True, help_text="The time period data collected or intended to represent. E.g '2001-2012'", max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='resource',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='resource', to='resources.resource'),
        ),
        migrations.RemoveField(
            model_name='resource',
            name='publisher',
        ),
        migrations.AddField(
            model_name='resource',
            name='owner',
            field=models.ManyToManyField(blank=True, to='resources.Owner'),
        ),
        migrations.AddField(
            model_name='resource',
            name='publisher',
            field=models.ManyToManyField(blank=True, to='resources.Publisher'),
        ),
        migrations.CreateModel(
            name='Collection',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150, unique=True)),
                ('keyword', models.ManyToManyField(to='resources.Category_Keywords')),
            ],
        ),
        migrations.AddField(
            model_name='resource',
            name='collection',
            field=models.ManyToManyField(blank=True, to='resources.Collection'),
        ),
        migrations.AlterField(
            model_name='resource',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='resource', to='resources.resource'),
        ),
        migrations.AddField(
            model_name='end_point',
            name='thumbnail',
            field=models.CharField(blank=True, help_text='The URL to a static image of the publisher', max_length=512, null=True),
        ),
        migrations.AlterField(
            model_name='resource',
            name='thumbnail',
            field=models.CharField(blank=True, help_text='The URL to a static image of the resource', max_length=512, null=True),
        ),
        migrations.AlterField(
            model_name='resource',
            name='type',
            field=models.ForeignKey(blank=True, help_text='The service type used to visualize the data in the browser', null=True, on_delete=django.db.models.deletion.SET_NULL, to='resources.type'),
        ),
        migrations.AddField(
            model_name='change_log',
            name='new',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
        migrations.AddField(
            model_name='change_log',
            name='old',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
        migrations.AlterField(
            model_name='change_log',
            name='date',
            field=models.DateTimeField(blank=True, default=datetime.datetime.now, verbose_name='Date changed'),
        ),
        migrations.CreateModel(
            name='Georeference_Request',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(blank=True, default=datetime.datetime.now, verbose_name='Date requested')),
                ('name', models.CharField(blank=True, max_length=200, null=True)),
                ('email', models.CharField(blank=True, max_length=200, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('resource', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='resources.resource')),
            ],
        ),
        migrations.CreateModel(
            name='Community_Input',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(blank=True, default=datetime.datetime.now, verbose_name='Date received')),
                ('name', models.CharField(blank=True, max_length=200, null=True)),
                ('email', models.CharField(blank=True, max_length=200, null=True)),
                ('field_name', models.CharField(max_length=100)),
                ('notes', models.TextField(blank=True, null=True)),
                ('resource', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='resources.resource')),
            ],
        ),
        migrations.AddField(
            model_name='change_log',
            name='community_input',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='resources.community_input'),
        ),
        migrations.AlterField(
            model_name='change_log',
            name='change_type',
            field=models.CharField(choices=[('o', 'origin'), ('a', 'automation'), ('u', 'user'), ('c', 'community')], max_length=1),
        ),
    ]
