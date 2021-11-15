"""
The sub class FileCollection_DS is used to handle dSPACE JSON collection file loading/saving, and database insert.
Starting from an Endpoint json file, this script traverses the pages of records and loading everything,
unless specific ID's are identified (see README for instructions).

TODO: the harvest script does not yet use the change management system and should be updated before production implementation

"""

from .FileCollection import FileCollection
import os.path
from os import path
from resources.models import Resource, Place, Category,Owner,Publisher,Type, Language,Category,Tag,Place,URL,URL_Type,Format
from datetime import datetime
import pytz


class FileCollection_DS(FileCollection):
    '''
    Control the REST requests and the passed params
    '''
    def __init__(self,props):
        # take the end point and start loading the data
        for p in props:
            setattr(self, p, props[p])

        print(self.end_point_url)
        self.open_prefix = self.end_point_url[:self.end_point_url.index("/rest")]
        print(self.open_prefix)
        super(FileCollection_DS, self).__init__(props)



    def load_results(self):
        """

        :return:
        """
        # declare the folder and file names
        folder_path=self.path+self.folder+"/"
        file=self.org_name+".json"
        _file = folder_path + file
        #check if the data exists
        url = self.end_point_url
        self.load_file_call_func( _file, url,'check_loaded')


    def check_loaded(self,data, parent_obj=False):
        """

        :param data:
        :param parent_obj:
        :return:
        """
        # scan the json looking for how many records have been downloaded
        # can setup the next request if there are more pages to be downloaded
        # print(data)
        self.drill_loaded_data(data)

    def drill_loaded_data(self, data):
        """

        :param data:
        :return:
        """
        # start by making sure a 'layers' folder exists
        layers_path = self.path + self.folder + "/layers"
        if not path.exists(layers_path):
            os.mkdir(layers_path)


        for index, r in enumerate(data['items']):
            # todo  - remove when done testing
            # if index >1:
            #     break

            _file = layers_path + "/" + r['handle'].replace("/","-") + ".json"
            _url = self.open_prefix+r['link']+"?expand=all"
            print(_file, _url)
            #
            self.load_file_call_func(_file, _url, 'check_sub_loaded', r)

    def check_sub_loaded(self,data,parent_obj):
        """

        :param data: the sub information to be used in creating more informative compound records
        :param parent_obj:
        :return:
        """

        self.ingest_record(data, parent_obj)


    def ingest_record(self,data,parent_obj):
        """

        :param data:
        :param parent_obj:
        :return:
        """

        obj = self.file_parser.create_record(parent_obj, data, self.open_prefix)

        if "dc.creator" in obj:
            owner, created = Owner.objects.get_or_create(name=obj['dc.creator'])
        else:
            owner = None

        if "dc.type" in obj:
            type, created = Type.objects.get_or_create(name=obj['dc.type'])
        else:
            type = None

        if "format" in obj:
            format, created = Format.objects.get_or_create(name=obj['format'])
        else:
            format = None

        if "dc.publisher" in obj:
            publisher, created = Publisher.objects.get_or_create(name=obj['dc.publisher'])
        else:
            publisher = None

        if "dc.title.alternative" not in obj:
            obj['dc.title.alternative'] = None

        if "dc.description.abstract" not in obj:
            obj['dc.description.abstract'] = ""

        if 'dc.date' not in obj or not obj['dc.date'].isdigit():
            obj['dc.date']=None

        try:
            r = Resource.objects.get(resource_id=obj['handle'], end_point=self.end_point)

        except Resource.DoesNotExist:
            r = Resource.objects.get_or_create(resource_id=obj['handle'],
                                               title=obj['dc.title'],
                                               alt_title=obj['dc.title.alternative'],
                                               # todo - support multi - dc.description
                                               description=obj['dc.description.abstract']+" "+ obj["description"],

                                               year=obj['dc.date'],
                                               thumbnail=obj['thumb'],
                                               license_info=obj['dc.rights'],

                                               access_information=obj['dcterms.rights.dpla'],
                                               # owner=owner,
                                               # publisher=publisher,
                                               type=type,
                                               format=format,
                                               harvest=self.harvest,
                                               end_point=self.end_point,
                                               raw_json="",
                                               layer_json=data,
                                               created=obj['dc.date.available'],
                                               accessioned=datetime.now(tz=pytz.UTC),
                                               )[0]
        #
        r.owner.add(owner)
        r.publisher.add(self.publisher)
        # # create the many to many objects then add them to the resource
        if 'langua' in obj:
            r.languages.add(Language.objects.get_or_create(name=obj['langua'])[0])
        for c in obj['categories']:
            r.category.add(Category.objects.get_or_create(name=c)[0])
        # for t in obj['tags']:
        #     r.tag.add(Tag.objects.get_or_create(name=t)[0])
        # for p in obj['places']:
        #     # note the place is unique on two columns so use both to avoid duplicates
        #     # todo - we will need another place table to store just the used values outside of the load list
        #     r.place.add(Place.objects.get_or_create(name=p))

        # and lastly - create the urls  by looping over the ones in the resources
        for u in obj['urls']:
            u_t, _ = URL_Type.objects.get_or_create(name=u['url_type'])
            URL.objects.get_or_create(url_type=u_t, url=u['url'], resource=r)

        return r