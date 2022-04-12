"""
The sub class FileCollection_CO is used to handle JSON from a custom source using ArcGIS server
This class should be modified to support your own unique system
"""

import os.path
from os import path
from .FileCollection import FileCollection
from datetime import datetime
import re

class FileCollection_CO(FileCollection):
    '''
    Control the REST requests and the passed params
    '''
    def __init__(self,props):
        # take the end point and start loading the data
        for p in props:
            setattr(self, p, props[p])

        self.total=None
        self.folder = self.org_name+"_"+self.date

        # same as
        arc_domain = "https://www.arcgis.com"
        self.arc_item_prefix = arc_domain + "/sharing/rest/content/items/"

        # self.arc_journal_prefix = arc_domain+"/apps/MapJournal/index.html?appid="
        # self.arc_webapp_prefix = arc_domain + "/apps/webappviewer/index.html?id="

        self.open_prefix = "https://opendata.arcgis.com/datasets/"
        self.api_types = ["Esri Rest API", "ArcGIS GeoServices REST API", "ArcGIS GeoService"]


        super(FileCollection_CO, self).__init__(props)


    def load_results(self):
        """

        :return:
        """
        # declare the folder and file names
        folder_path=self.path+self.folder+"/"
        file=self.org_name+".json"
        _file = folder_path + file
        self.load_file_call_func( _file, self.end_point_url ,'check_loaded')

    def check_loaded(self,data,parent_obj=False):
        """

        :param data:
        :param parent_obj:
        :return:
        """
        # scan the json looking for how many records have been downloaded
        self.drill_loaded_data(data)

    def drill_loaded_data(self,data):
        '''
        perform a basic drill down operation looking through the results and loading the attributes
        :param data:
        :return:
        '''
        # start by making sure a 'layers' folder exists
        layers_path=self.path+self.folder+"/layers"
        if not path.exists(layers_path):
            os.mkdir(layers_path)

        root_domain = self.end_point_url[:self.end_point_url.rindex("/")]

        for r in data['layers']:

            # download the file url+'/layers?f=pjson' - create records for each and associate these records with the parent
            _r=r['layer']
            _r["id"] = _r["Nid"]

            _r["url"] = _r["URL"]

            del _r["URL"]
            if _r["url"].find("https://")==-1:
                _r["url"]=root_domain+_r["url"]

            _r["urls"]=[]
            _r["urls"].append({'url_type': "mapserver", 'url': _r["url"]})

            if self.resource_ids:
                # only load specified resource ids

                for r_id in self.resource_ids:
                    if r_id ==  _r["id"]:
                        print("Loading....", _r["id"])
                        self.load_data( _r["url"]+"?f=pjson",_r["id"], _r, layers_path)
            else:
                self.load_data(_r["url"] + "?f=pjson", _r["id"], _r, layers_path)



    def load_data(self, _url,id, r, layers_path):
        """

        :param _url:
        :param id:
        :param r:
        :param layers_path:
        :return:
        """
        _file = layers_path + "/" + id + ".json"

        # we need to pass a reference to the parent
        print("The URL is...",_url)
        self.load_file_call_func(_file, _url, 'ingest_parent_record', r)

    def add_details(self,data, stub):
        if 'Layer Description' in data:
            # get the date from the layer description
            regex = "\d{8}"
            match = re.findall(regex, data['Layer Description'])
            if len(match) > 0:
                stub["modified"] = int(match[0])

            # get an acronym if it exists
            regex = "\w[A-Z]{2,}[A-Za-z]*"
            match = re.findall(regex, data['Layer Description'])
            if len(match) > 0:
                stub["owner"] = match[0]

        return stub

    def ingest_parent_record(self, data, parent_data):
        """

        :param data:
        :param parent_data:
        :return:
        """
        root_domain = self.end_point_url[:self.end_point_url.rindex("/")]

        obj=data.copy()

        # if there are child records just create the parent
        if len(data["layers"]) == 1:
            data["id"] = parent_data["id"]
            obj = self.file_parser.create_record(parent_data,data, self)

        # put what we have in it's place
        obj['description']=self.convert_urls(parent_data["Layer Description"],root_domain)
        obj['title'] = parent_data["Title"]

        obj['name'] = ""
        obj['thumb'] = ""
        obj['licenseInfo'] = ""
        obj['accessInformation'] = ""
        obj['licenseInfo'] = ""
        obj["urls"]=parent_data["urls"]
        obj["id"] = parent_data["id"]

        obj["urls"].append({'url_type': "info_page", 'url': root_domain })


        obj = self.add_details(parent_data, obj)



        # create a parent object
        r = self.save_record(obj, parent_data, data)
        parent_data['parent_resource']=r
        self.check_sub_loaded(data, parent_data)


    def check_sub_loaded(self, data, parent_data):
        """

        :param data:
        :param parent_data:
        :return:
        """
        # now create the children of the parent
        # loop over the layers
        # and generate the url to the sub service
        layers_path = self.path + self.folder + "/layers"

        for l in data["layers"]:
           # make sure there is than 1 child
           if len(data["layers"])>1:
            _id=str(l["id"])
            child_url=parent_data["url"]+"/"+_id+"?f=pjson"
            _file = layers_path+"/"+parent_data['id']+"_"+ _id+"_service.json"
            self.load_file_call_func(_file, child_url, 'ingest_child_record', parent_data.copy())



    def ingest_child_record(self, data, parent_data):
        """

        :param data:
        :param parent_data:
        :return:
        """
        # if type is group ignore
        if "type" in data and data["type"]=="Group Layer":
            return

        data = self.add_details(parent_data, data)


        child_obj = self.file_parser.create_record(parent_data,data, self)
        child_obj['id']=str(parent_data['id'])+"_"+str(data['id'])
        child_obj["urls"].append({'url_type': data["type"].lower(), 'url': parent_data["url"]+"/"+str(data['id'])})
        child_obj['title']= data['name']
        # retain the parent outside of the object
        r = parent_data['parent_resource']
        # remove the parent so that it's not stored
        del parent_data['parent_resource']
        print("we are working with ", child_obj['id'])
        # pass the child_data to be stored as the layer_json in the record
        self.save_record(child_obj, parent_data, data, r)


