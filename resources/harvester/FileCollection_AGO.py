"""
The sub class FileCollection_AGO is used to handle JSON ArcGIS Online public file loading/saving and database insert.
Starting from an Endpoint json file, this script traverses the pages of records and loading everything,
unless specific ID's are identified (see README for instructions).
This is great for seeding a database with resources, as all the layers will be loaded maintaining the parent child relationships.

It should be noted that in academic settings, ArcGIS Online may contain many classroom assignments which likely should not be shared through this platform.

"""

import os.path
from os import path
from .FileCollection import FileCollection

class FileCollection_AGO(FileCollection):
    '''
    Control the REST requests and the passed params
    '''
    def __init__(self,props):
        # take the end point and start loading the data
        for p in props:
            setattr(self, p, props[p])

        self.start=1
        self.page = 1
        self.total=None
        self.folder = self.org_name+"_"+self.date

        # same as FileCollection_DCAT - consider storing at higher level
        arc_domain = "https://www.arcgis.com"
        self.arc_item_prefix = arc_domain + "/sharing/rest/content/items/"

        # self.arc_journal_prefix = arc_domain+"/apps/MapJournal/index.html?appid="
        # self.arc_webapp_prefix = arc_domain + "/apps/webappviewer/index.html?id="

        self.open_prefix = "https://opendata.arcgis.com/datasets/"
        self.api_types = ["Esri Rest API", "ArcGIS GeoServices REST API", "ArcGIS GeoService"]

        super(FileCollection_AGO, self).__init__(props)


    def load_results(self):
        """

        :return:
        """
        # declare the folder and file names
        folder_path=self.path+self.folder+"/"
        file=self.org_name+"_p"+str(self.page)+".json"
        _file = folder_path + file
        #check if the data exists
        url = self.end_point_url + "&start=" + str(self.start) + "&num=" + str(self.num)
        self.load_file_call_func( _file, url,'check_loaded')



    def check_loaded(self,data,parent_obj=False):
        """

        :param data:
        :param parent_obj:
        :return:
        """
        # scan the json looking for how many records have been downloaded
        # can setup the next request if there are more pages to be downloaded
        print(data["total"])
        # if there's more data to download - increment the page num and start values
        # todo - uncomment below to load all pages.
        #  Note: there could be thousands of records for academic institutions!!!
        # if (data["nextStart"] !=-1):
        #     self.start=data["nextStart"]
        #     self.page+=1
        #     self.load_results()

        self.drill_loaded_data(data)


        # todo add else for when all done and print the results
        #  - this previously generated a CSV report but we now use a database

        # once all the files have been loaded we should check the results
        # self.file_parser.get_results(self.path+self.report_file)

    def drill_loaded_data(self,data):
        '''
        perform a basic drill down operation looking through the results and loading the attributes
        :param data: The JSON file to traverse
        :return:
        '''
        # start by making sure a 'layers' folder exists
        layers_path=self.path+self.folder+"/layers"
        if not path.exists(layers_path):
            os.mkdir(layers_path)

        # loop over the results and load each
        for r in data['results']:
            # download the file url+'/layers?f=pjson' - create records for each and associate these records with the parent
            print(r['url'])
            format = r['type']

            # r["publisher"] = self.publisher # to be pulled from json response

            id= r['id']
            if r['url'] is not None:

                if self.resource_ids:
                    # only load specified resource ids
                    for r_id in self.resource_ids:
                        if r_id == id:
                            print("Loading....", r_id)
                            self.load_data(id, r, layers_path)


                # filter by format - we might also want other types of resources in the future
                elif format not in ["Web Mapping Application","StoryMap"]:
                    # download the file and create records
                    self.load_data(id, r, layers_path)
                else:
                    # # artificially add an extent for records that don't have one
                    # # todo - need to flag this value for manual inspection
                    # if len(r["extent"]) == 0:
                    #     r["extent"] = [[-125.102, 23.9979992], [-66.134, 50.1019992]]
                    #     self.file_parser.create_record(r)
                    pass

            else:
                print("no record created for type", type)

    def load_data(self, id, r, layers_path):
        """

        :param id:
        :param r:
        :param layers_path:
        :return:
        """
        _file = layers_path + "/" + id + ".json"
        _url = self.arc_item_prefix + id + "/layers?f=pjson"
        # we need to pass a reference to the parent
        print("The URL is...",_url)
        self.load_file_call_func(_file, _url, 'ingest_parent_record', r)


    def ingest_parent_record(self, data, child_data):
        """
        Create a parent object
        :param data:
        :param child_data:
        :return:
        """
        obj = self.file_parser.create_record(data, False, self)
        r = self.save_record(obj, child_data, data)

        # look for child record if "Singlelayer" is not found in typeKeywords
        if "typeKeywords" in data and "Singlelayer" not in data["typeKeywords"]:

            # create a child associated with the parent

            # store the base url
            layers_path = self.path + self.folder + "/layers"
            _id = child_data['id']
            _file = layers_path + "/" + _id + "_service.json"

            if "url" in child_data:
                _url = child_data["url"] + "?f=pjson"
                print("child found", _url)
                child_data['parent_resource'] = r
                self.load_file_call_func(_file, _url, 'check_sub_loaded', child_data)

    def check_sub_loaded(self, data, parent_data):
        """
        Create the children of the parent
        :param data:
        :param parent_data:
        :return:
        """
        # loop over the layers
        # and generate the url to the sub service
        layers_path = self.path + self.folder + "/layers"
        for l in data["layers"]:
            # make sure there is than 1 child
            if len(data["layers"]) > 1:
                _id=str(l["id"])
                child_url=parent_data["url"]+"/"+_id+"?f=pjson"
                _file = layers_path+"/"+parent_data['id']+"_"+ _id+"_service.json"
                self.load_file_call_func(_file, child_url, 'ingest_child_record', parent_data.copy())


    def ingest_child_record(self, data, parent_data):
        """
        Create the child record
        :param data:
        :param parent_data:
        :return:
        """

        child_obj = self.file_parser.create_record(parent_data,data, self)

        # manually adjust the supplied names to conform with the database insert
        child_obj['id']=str(parent_data['id'])+"_"+str(data['id'])
        child_obj["urls"].append({'url_type': data["type"], 'url': parent_data["url"]+"/"+str(data['id'])})
        child_obj['title']= data['name']
        # retain the parent outside of the object
        r = parent_data['parent_resource']
        # remove the parent so that it's not stored
        del parent_data['parent_resource']
        print("we are working with", child_obj['id'])
        # pass the child_data to be stored as the layer_json in the record
        self.save_record(child_obj, parent_data, data, r)


