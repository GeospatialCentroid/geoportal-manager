from django.core.management.base import BaseCommand
from resources.models import Resource
from datetime import datetime
import os.path
import time
from os import path
import glob

import resources.ingester.DB_ToGBL as db_to_gbl
import resources.ingester.Publish_ToGBL as publish_to_gbl

directory = os.path.dirname(os.path.realpath(__file__))+"/../../ingester"

class Command(BaseCommand):
    """
    This is a two step process -
    1) creates all the json files for solr ingest
    2) ingests to the server of choice - local, staging, prod

    called via -  python manage.py ingest -s

    status options include
    ('as', 'Approved for Staging'),
        ('is', 'In Staging'),
        ('ap', 'Approved for Production'),
        ('ip', 'In Production'),
        ('nr', 'Needs Review')

    """
    help = 'Ingests data into Solr'

    def add_arguments(self, parser):

        parser.add_argument("-s", "--status", help="select all the records, default is only approved will be selected",)
        parser.add_argument("-n", "--no_promote", action='store_true',
                            help="Prevent records from being promoted in status", )
        parser.add_argument("-e", "--end_point_id", type=int, help="specify an End Point ID")
        parser.add_argument("-r", "--resource_ids", type=str,
                            help="(Optional) If there are one or more resource ids you would like choose to ingest from a known endpoint. Use comma separation.", )

        #todo allow specific collections, file types, etc
        # we might also want to run


    def handle(self, *args, **kwargs):
        """
        Select all the records marked as approved (can be ignored)
        :param args:
        :param kwargs:
        :return:
        """
        verbosity = kwargs['verbosity']
        print ("verbosity", kwargs['verbosity']) # defaults to 1

        # clear the contents of a directory
        if path.exists(directory + "/json"):
            files = glob.glob(directory + "/json/*")
            if (verbosity>1):
                print("removing existing files from past ingest for a fresh start!")

            for f in files:
                os.remove(f)
        if (verbosity > 1):
            print("Retrieving all Resources with status of", kwargs['status'])

        if kwargs['resource_ids']:
            r_ids=kwargs['resource_ids'].split(",")
            resources=[]
            for r_id in r_ids:
                #  should an endpoint also be specified
                if kwargs['end_point_id']:
                    resources = Resource.objects.filter(resource_id=r_id, end_point=kwargs['end_point_id'],
                                                        parent__isnull=True)
                else:
                    resources.append(Resource.objects.get(resource_id=r_id,parent__isnull=True))
        elif kwargs['end_point_id']:
            resources = Resource.objects.filter(status_type=kwargs['status'],end_point=kwargs['end_point_id'],parent__isnull=True)
        else:
            resources = Resource.objects.filter(status_type=kwargs['status'],parent__isnull=True)

        # check for children
        # todo consider having child status either the same or better e.g
        # ('as', 'Approved for Staging'),
        # ('is', 'In Staging'),
        # ('ap', 'Approved for Production'),
        # ('ip', 'In Production'),

        for r in resources:
            print("Getting child layers for:",r.id,"with status",kwargs['status'])
            r.layers = Resource.objects.filter(status_type=kwargs['status'],parent=r.id)
            print("The layers are:",r.layers)


        # for each resource create a json file
        exporter = db_to_gbl.DB_ToGBL({
            "resources":resources,
            "path": directory + "/",
            "verbosity":verbosity
        })

        # now that the files have been created - PUBLISH!
        publish_to_gbl.Publish_ToGBL({
            "path": directory + "/json",
            "verbosity":verbosity
        })

        # we also need to update the records that have been added to the solr db
        # so long as no_promote is set
        if kwargs['no_promote'] is None:
            new_status=""
            if kwargs['status'] =="as": # 'Approved for Staging'
                new_status = "is" # 'In Staging'
                r.stage_date = datetime.now()

                #do the same for the children
                for l in r.layers:
                    l.stage_date =  r.stage_date

            if kwargs['status'] =="ap": # 'Approved for Production'
                new_status = "ip" # 'In Production'
                r.production_date = datetime.now()

                # do the same for the children
                for l in r.layers:
                    l.production_date = r.production_date


            for r in resources:
                r.status_type=new_status
                r.save()

                # and save the children
                for l in r.layers:
                    l.status_type = r.status_type
                    l.save()

