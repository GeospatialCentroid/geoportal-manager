"""
The sub class FileCollection_DCAT is used to handle JSON ArcGIS Hub DCAT public file loading/saving and database insert.
Starting from an Endpoint json file, this script traverses the pages of records and loading everything,
unless specific ID's are identified (see README for instructions).

"""

from .FileCollection import FileCollection
import os.path
from os import path

class FileCollection_DCAT(FileCollection):
    '''
    Control the REST requests and the passed params
    '''
    def __init__(self,props):
        # take the end point and start loading the data
        for p in props:
            setattr(self, p, props[p])

        arc_domain = "https://www.arcgis.com"
        self.arc_item_prefix = arc_domain + "/sharing/rest/content/items/"

        # self.arc_journal_prefix = arc_domain+"/apps/MapJournal/index.html?appid="
        # self.arc_webapp_prefix = arc_domain + "/apps/webappviewer/index.html?id="

        self.open_prefix = "https://opendata.arcgis.com/datasets/"
        self.api_types= ["Esri Rest API","ArcGIS GeoServices REST API","ArcGIS GeoService"]

        super(FileCollection_DCAT, self).__init__(props)



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
        #print(data)
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


        for index, r in enumerate(data['dataset']):

            # create a parent record by extracting the identifier
            # everything after the last slash and before the underscore
            _id = r['identifier']
            try:
                id = _id[_id.rindex('/')+1:_id.rindex('_')]
            except:
                id = _id[_id.rindex('/')+1:]
            # KW 20230309 ESRI has changed their identifier
            if "id=" in id:
                id=id[id.index("id=")+3:]
            if "&" in id:
                id = id[:id.index("&")]

            r['identifier']=id
            #######
            # todo  - remove when done testing - should be 'arg' flag
            # if index >1:
            #     break
            ###############
            if self.resource_ids:
                # only load specified resource ids
                for r_id in self.resource_ids:
                    if r_id == id:
                        print("Loading....",r_id)
                        self.load_data( id,r, layers_path)
            else:
                self.load_data(id,r, layers_path)




    def load_data(self,id,r,layers_path):
        """

        :param id:
        :param r:
        :param layers_path:
        :return:
        """
        _file = layers_path + "/" + id + ".json"
        _url = self.arc_item_prefix + id + "/layers?f=pjson"
        self.load_file_call_func(_file, _url, 'ingest_parent_record', r)


    def ingest_parent_record(self,data,child_data):
        """

        :param data:
        :param child_data:
        :return:
        """

        obj = self.file_parser.create_record(data,False, self)
        print(obj)
        # create a parent object
        r = self.save_record(obj,child_data,data)

        # loop over the distribution and load the listed 'accessURL'
        for d in child_data['distribution']:

            if d["title"] in  self.api_types:
                # store the base url
                layers_path = self.path + self.folder + "/layers"
                _id = child_data['identifier']
                id = _id#[_id.rindex('/'):]
                _file = layers_path + "/" + id + "_service.json"

                if "accessURL" in d:
                    _url = d["accessURL"] + "?f=pjson"
                    print("child found",_url)
                    child_data['parent_resource']=r
                    self.load_file_call_func(_file, _url, 'ingest_child_record', child_data)


    def ingest_child_record(self,data,child_data):
        """

        :param data:
        :param child_data:
        :return:
        """

        # now create the child of the parent
        child_obj = self.file_parser.create_record(data, child_data, self)

        # retain the parent outside of the object
        r = child_data['parent_resource']
        # remove the parent so that it's not stored in the json field
        del child_data['parent_resource']

        # pass the child_data to be stored as the layer_json in the record
        self.save_record(child_obj,child_data,data, r)


