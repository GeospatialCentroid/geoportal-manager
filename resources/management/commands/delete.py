from django.core.management.base import BaseCommand
from resources.models import Resource
from datetime import datetime
import os.path
import time

import resources.ingester.Delete_From_Solr as Delete_From_Solr


directory = os.path.dirname(os.path.realpath(__file__))+"/../../ingester"

class Command(BaseCommand):
    """
        delete records from solr

        We'll need to flag records from postgres and then remove them from the solr index
    """
    help = 'Delete data into Solr'

    def add_arguments(self, parser):

        parser.add_argument("-s", "--status", help="select the status of record to delete - most likely 'rs' or 'rp'",)
        parser.add_argument("-n", "--no_promote", action='store_true',
                            help="Prevent record status from being updated", )

        parser.add_argument("-r", "--resource_ids", type=str,
                            help="(Optional) If there are one or more resource ids you would like choose to delete. Use comma separation.", )



    def handle(self, *args, **kwargs):
        """
            Delete the choosen records
        """
        print("Retrieving all Resources with status of", kwargs['status'])
        deleter = Delete_From_Solr.Delete_From_Solr({ })

        # delete all the records
        if  kwargs['status'] =='all':
            print("delete_everything? y/n")
            choice = input().lower()
            if choice=='y':
                deleter.interface.delete_everything("")
            return


        if (kwargs['resource_ids']):
            r_ids = kwargs['resource_ids'].split(",")
            for r_id in r_ids:
                # note that ids in the solr database area composite fo the resource_id + the end_point
                deleter.interface.delete_one_record(r_id)
                #todo - update the status of the resource
            return

        else:
            resources = Resource.objects.filter(status_type=kwargs['status'])


        for r in resources:
            deleter.interface.delete_one_record(r.resource_id)
            print(r.resource_id, "DELETED")


        # For those that have been flagged for deletion
        # change status to 'removed from Solr'
        # so long as no_demote is set
        if kwargs['no_promote'] is None:
            for r in resources:
                r.status_type='nr'
                r.save()