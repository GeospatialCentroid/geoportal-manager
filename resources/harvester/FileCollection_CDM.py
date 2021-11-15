"""
The sub class FileCollection_CDM is used to handle JSON from CONTENTdm file loading/saving and database insert.
Starting from an Endpoint json file, this script traverses the pages of records and loading everything,
unless specific ID's are identified (see README for instructions).

It should be noted that CONTENTdm uses a flexible structure for it's metadata so your mileage may vary.
It should also be noted that CONTENTdm deals more with static images and some use IIIF.
Some documentation on saving Geospatial metadata for with a CONTENTdm record can be found here
http://csucontentdm.pbworks.com/w/page/145734930/Geospatial%20Metadata%20Documentation

Adding geospatial data to a harvested resource can be done via the Admin system that accompanies this platform.
This is important for spatial search.

"""

from .FileCollection import FileCollection
import os.path
from os import path
class FileCollection_CDM(FileCollection):
    '''
    Control the REST requests and the passed params
    '''
    def __init__(self,props):
        # take the end point and start loading the data
        for p in props:
            setattr(self, p, props[p])

        self.open_prefix = self.end_point_url[:self.end_point_url.index("/api")]

        super(FileCollection_CDM, self).__init__(props)



    def load_results(self):
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
            id = r['itemId']

            if self.resource_ids:
                # only load specified resource ids
                for r_id in self.resource_ids:

                    if r_id == id:
                        print("Loading", r_id)
                        self.load_data(id, r, layers_path)

            else:
                self.load_data(id, r, layers_path)

    def load_data(self,id,r,layers_path):
        """

        :param id:
        :param r:
        :param layers_path:
        :return:
        """
        _file = layers_path + "/" + id + ".json"
        # use the 'thumbnailUri' excluding the end to consistently load metadata for both 'compoundobject' and 'singleitem'
        _url = self.open_prefix + r['thumbnailUri'][:r['thumbnailUri'].index("/thumbnail")]
        print(_url)
        self.load_file_call_func(_file, _url, 'check_sub_loaded', r)

    def check_sub_loaded(self,data,parent_obj):
        """
        We're going a level deeper here and looking at the layers associated with a record
        We'll create only parent records and associate the children (if they exist beneath).

        :param data: the sub information to be used in creating more informative compound records
        :param parent_obj:
        :return:
        """

        parent = self.ingest_parent_record(data, parent_obj)

        layers_path = self.path + self.folder + "/layers"

        if "page" in data['objectInfo']:
            print("There are children here")

            # todo - associate the children - all details exist in the 'data'
            #generate urls for all children
            root_path = self.open_prefix+data['thumbnailUri'][:data['thumbnailUri'].index("/id/")+4]

            for index, p in enumerate(data['objectInfo']["page"]):

                # todo get the parent id
                # create a child resource with only new information - the ingest should take the parent info and combine it with the child
                parent_id = parent_obj["itemId"]
                item_id = p["pageptr"]
                _file = layers_path + "/" + parent_id + "_sub_"+item_id+".json"
                _url = root_path+item_id
                # todo - decide if we want to save the 3  metadata files
                self.load_file_call_func(_file, _url, 'check_sub_sub_loaded', parent)


    def check_sub_sub_loaded(self,data, parent_obj):
        """

        :param data:
        :param parent_obj:
        :return:
        """
        # now that we've loaded the child information - create
        self.ingest_child_record(data, parent_obj)

    def ingest_parent_record(self,data,parent_obj):
        """

        :param data:
        :param parent_obj:
        :return:
        """
        # todo - support: subjec,physic

        obj = self.file_parser.create_record(parent_obj, data, self.open_prefix)


        return self.save_record(obj, parent_obj, data)

    def ingest_child_record(self,data,parent_obj):
        """

        :param data:
        :param parent_obj:
        :return:
        """
        obj = self.file_parser.create_record(None, data, self.open_prefix)
        return self.save_record(obj, data,None,parent_obj)
