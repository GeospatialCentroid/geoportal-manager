from django.core.management.base import BaseCommand
from resources.models import End_Point, Place, Category,Harvest
from datetime import datetime

import os.path
import time

import resources.harvester.FileManager as fm

file_manager = None

directory = os.path.dirname(os.path.realpath(__file__))+"/../../harvester"
report_file = "report.csv" # this is temporary but may be useful

# create a command accessible via the manage.py interface
# ref https://simpleisbetterthancomplex.com/tutorial/2018/08/27/how-to-create-custom-django-management-commands.html
class Command(BaseCommand):
    help = 'Harvests data from End Points'
    # example call -  python manage.py harvest -d 20210312
    # or if you are using GIT to keep track of harvested data - better to over write with
    # python manage.py harvest -d '' -e 4 -o
    # depending on the end-point type specific methods need to be implemented e.g ArcGIS Online, CONTENTdm, etc

    def add_arguments(self, parser):

        parser.add_argument("-l", "--local", help="choose if local run",
                            action="store_true",)

        parser.add_argument("-e", "--end_point_id", type=int, help="specify an End Point ID")

        parser.add_argument("-d", "--date", type=str,
                            help="(Optional) The date of when to run - useful when wanting to overwrite the run date. Format YYYYMMDD. Could use '' for no date tracking.",)

        parser.add_argument("-o", "--overwrite", action="store_true",
                            help="(Optional) The default is to ignore local files that exist. Use this flag to overwrite local files", )

        parser.add_argument("-r", "--resource_ids", type=str,
                            help="(Optional) If there are one or more resource ids you would like choose to harvest from a known endpoint. Use comma separation.", )


    def handle(self, *args, **kwargs):
        print(kwargs)
        # should date tracking be requested add and '_' for cleaner file names
        if (kwargs['date']):
            _date = '_'+kwargs['date']
        elif kwargs['date']=='':
            _date = kwargs['date']
        else:
            _date = '_'+time.strftime('%Y%m%d')

        if (kwargs['resource_ids']):
            kwargs['resource_ids'] = kwargs['resource_ids'].split(",")

        harvest, created= Harvest.objects.get_or_create(trigger_type='u', date =datetime.now())
        file_manager = fm.FileManager({
            "data_folder": "data",
            "num": 100,  # the number of records to collect with each iteration (max 100 determined by Esri)
            "date": _date,
            "overwrite": kwargs['overwrite'],
            "resource_ids": kwargs['resource_ids'],
            "path": directory + "/",
            "categories": Category.objects.all(),
            "places": Place.objects.all(),
            "report_file": report_file,

        })

        # get the end points from the data base and loop over them
        if (kwargs['end_point_id']):
            end_points = [End_Point.objects.get(pk=kwargs['end_point_id'])]
        else:
            end_points = End_Point.objects.all()

        if end_points is not None:
            for e in end_points:
                # load each end_point
                # inject the data
                print(e)

                row ={}
                row["date"]=file_manager.date
                row["path"] = file_manager.path+"/"+file_manager.data_folder+"/"
                row["num"] = file_manager.num
                row["report_file"] = file_manager.report_file
                row["end_point_url"]=e.url
                row["org_name"] = e.org_name
                row["publisher"] = e.publisher
                row["end_point"] = e
                row["overwrite"] = file_manager.overwrite
                row["resource_ids"] = file_manager.resource_ids
                row["harvest"] = harvest # a reference to the database harvest record to track the progress
                row["end_point_type"] = e.end_point_type
                # create the file collection
                print(row)
                file_manager.load(row)
        else:
            print("No end points found")

        print("directory:",directory)