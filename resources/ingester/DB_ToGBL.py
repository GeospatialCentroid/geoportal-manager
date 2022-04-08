import csv
import json
import os
from datetime import datetime
from .. import utils
from django.forms.models import model_to_dict
import pytz

class DB_ToGBL:
    '''
    Take records from the database and generate a json file for later ingestion into Solr
    The flow of events starts with parent records
    Information from parent records is used to generate a GeoBlacklight schema json structure
        Within this each parent record - could exist child records
            These child records retain the information of the parent and overwrite with any of their own information

    '''
    def __init__(self,props):
        for p in props:
            setattr(self, p, props[p])

        # makes a folder to store the export - if it doesn't exist
        if not os.path.exists(self.path+"json/"):
            os.mkdir(self.path+"json/")

        self.single_dict = {  # dictionary to translate single-value Dublin Core/GBL fields into GBLJson
            "resource_id": ["id", "dct_identifier_sm"],
            # "Status": ["b1g_status_s"],
            # "Date Accessioned": ["b1g_dateAccessioned_s"],
            # "Date Retired": ["b1g_dateRetired_s"],

            # "Accrual Method": ["dct_accrualMethod_s"],
            "title": ["dct_title_s"],

            # we're only supporting one alterate title but could be '|' separator
            "alt_title": ["dct_alternativeTitle_sm"],
            "description": ["dct_description_sm"],

            "year": ["gbl_indexYear_im"],
            # "owner": ["schema_provider_s"],
            "format": ["dct_format_s"],
            "geometry_type": ["gbl_resourceType_sm"],
            # replaced  was "type: and "dc_type_sm" as it's more for the the service type

            # "Layer ID": ["gbl_wxsIdentifier_s"],
            "thumbnail": ["thumbnail_path_ss"],

            "temporal_coverage": ["dct_temporal_sm"],
            "license_info": ["dct_rights_sm"],


        }
        self.multiple_dict = {  # dictionary to translate multivalue Dublin Core/GBL fields into GBLJson

            "category": ["dct_subject_sm"],
            "tag": ["dcat_keyword_sm"],

            "named_place": ["dct_spatial_sm"],
            # todo use owner 'full_name' if available
            "owner": ["dct_creator_sm"],
            "publisher": ["dct_publisher_sm"],

            "languages": ["dct_language_sm"],

        }

        for r in self.resources:
            self.export(r)

    def map_data(self, data, stub):
        """

        :param data:
        :param stub:
        :return:
        """
        for sd in self.single_dict:
            for v in self.single_dict[sd]:
                val = getattr(data, sd)
                if val:
                    stub[v] = str(val)

            # now do the multi dictionary values and separate by '|'
        for md in self.multiple_dict:
            for v in self.multiple_dict[md]:
                li = []
                for m in getattr(data, md).all():
                    # this relies on the fact that 'name' or 'full' be present in each of the model objects
                    if hasattr(m, 'full_name') and m.full_name != None and m.full_name != "":
                        li.append(m.full_name)
                    elif m.name:
                        li.append(m.name)
                stub[v] = li

        return stub

    def export(self,r):

        print("Resource- coming down the ramp")
        # created = models.DateTimeField('Date created', null=True, blank=True)
        # accessioned = models.DateTimeField('Date accessioned', null=True, blank=True)
        # license_info = RichTextField(null=True, blank=True)

        # harvest = models.ForeignKey(Harvest, on_delete=models.SET_NULL, null=True, blank=True)

        # parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, related_name='resource')
        #
        # access_information = models.TextField(null=True, blank=True)

        if self.verbosity>0:
            print(r.publisher)

        # a list of attributes that map to the json output
        #todo - updated id to be persistent identifier - https://github.com/geoblacklight/geoblacklight/wiki/GeoBlacklight-1.0-Metadata-Elements
        # make unique
        r.resource_id+="-"+str(r.end_point.id)


        sub_folder = "" # consider setting this to better organize records

        pub_date=None;
        date_str_fmt="%Y-%m-%dT%H:%M:%SZ"
        # start with the published date
        if r.created is not None:
            pub_date = r.created.strftime(date_str_fmt)

        if r.modified is not None:
            pub_date= r.modified.strftime(date_str_fmt)

        if not pub_date and hasattr(r, 'year'):
            pub_date = r.year

        # create a parent container "p_data" to store the details
        #todo - make the rights more flexible

        p_data = {"gbl_mdVersion_s": "Aardvark",
                  "gbl_mdModified_dt": datetime.now().strftime(date_str_fmt),
                  "dct_issued_s": pub_date,
                  "dct_accessRights_s": "Public"}  # starting dictionary with set values - could also be "Restricted"

        # take all the single dictionary items and map the associated database values to them
        p_data = self.map_data(r, p_data)

        for sd in self.single_dict:
            for v in self.single_dict[sd]:
                val =getattr(r, sd)
                if val:
                    p_data[v] = str(val)

        # now do the multi dictionary values and separate by '|'
        for md in self.multiple_dict:
            for v in self.multiple_dict[md]:
                li =[]
                for m in getattr(r, md).all():
                    # this relies on the fact that 'name' or 'full' be present in each of the model objects
                    if hasattr(m, 'full_name') and m.full_name!=None and m.full_name!="":
                        li.append(m.full_name)
                    elif m.name:
                        li.append(m.name)
                p_data[v] = li

        # store bounding box, centerpoint, and area (for sorting)
        if r.bounding_box:
            p_data["dcat_bbox"] = self.get_bounds(r.bounding_box)
            #todo resolve error Solr Error: Solr responded with an error (HTTP 400): [Reason: ERROR: [doc=87-6] Error adding field 'dcat_centroid'='-105.5665780808026,40.63192715262816' msg=Unable to parse shape given formats "lat,lon", "x y" or as WKT because java.text.ParseException: Unknown Shape definition [-105.5665780808026,40.63192715262816]]
            p_data["dcat_centroid"] = str(" ".join(list(map(str,r.bounding_box.centroid.coords))))
            p_data["geom_area"] =r.bounding_box.area
            #required to store the corners for image placement
            # check for coplanarity - and if so use the envelop instead of the polygon
            if(int(r.bounding_box.centroid.coords[0]) ==0 or int(r.bounding_box.centroid.coords[0]) ==0) or r.bounding_box.area==0:
                p_data["locn_geometry"] =  p_data["dcat_bbox"]
            else:
                p_data["locn_geometry"] = self.get_poly(r.bounding_box)


        # store the list of references for injection
        ref = self.get_refs(r.url_set.all(), str(r.type))
        p_data["dct_references_s"] = '{' + (','.join(ref)) + '}'
        print(p_data["dct_references_s"])
        if self.verbosity > 1:
            print(ref, "ref")



        p_data["lyr_count"] = len(r.layers)

        p_data["solr_type"] = "parent"
        p_data["gbl_suppressed_b"] = False

        #---------------------------------

        print(r.resource_id," has ",len(r.layers),"layers")

        # create a list to store the children
        child_docs=[]
        # default setting for a parent
        is_parent=False

        # should the parent have only one child - the parent becomes the child
        if len(r.layers) == 1:
            is_parent=True

        # when there are children - store them in the 'child_docs' list
        if len(r.layers)>0:
            for l in r.layers:
                # start with the parent
                child_docs.append(self.generate_child_record(p_data.copy(),l,r,is_parent))

        if len(child_docs)>1:
            # add the children to the parent

            p_data["_childDocuments_"] = child_docs
            # remove parent urls
            # p_data["dct_references_s"]={}

        elif len(child_docs)==1:
            # make the parent a child
            p_data = child_docs[0]
            print("Use the child record instead of the parent")

            p_data["solr_type"] = "parent"

            if p_data is not None:
                if "drawingInfo" in p_data:
                    p_data["drawing_info"] = p_data["drawingInfo"]
                if "drawing_info" in p_data:
                    p_data["drawing_info"]=json.dumps(p_data["drawing_info"])
                # if "fields" in p_data:
                #     # and get the fields from the child
                #     p_data["fields"]=p_data["fields"]

        if r.layer_json and 'drawingInfo' in r.layer_json:
            p_data["drawing_info"] = json.dumps(r.layer_json["drawingInfo"])

        if r.layer_json and 'fields' in r.layer_json:
            p_data["fields"] = json.dumps(r.layer_json["fields"])

        # set the json file name
        filename = r.resource_id.replace('/', '_') + ".json"
        # create a sub directory should one be set
        if not os.path.exists(self.path + "json/"+sub_folder):
            os.mkdir(self.path + "json/"+sub_folder)


        with open(self.path+"json/" + sub_folder + "/" + filename,
                  'w') as jsonfile:  # writes to a json with the identifier as the filename
            json.dump(p_data, jsonfile, indent=2)




    def generate_child_record(self,l_data,_l,r,is_parent=False):
        """
        Create a child record
        :param l_data: The dict to start adding too - prepopulated
        :param _l: child record
        :param r: parent record
        :param make_parent: boolean flag to
        :return: modified child dict
        """
        print("Generate child record...")

        # update the layer count since children will only have one layer
        l_data['lyr_count'] = 1

        is_child_record=False
        if type(_l) == type(r):
            # keep track of the fact that this is a record so the urls aren't tampered with
            is_child_record = True
            print(_l)
            ref = self.get_refs(_l.url_set.all(), str(r.type))  # store the list of references for injection
            if self.verbosity > 1:
                print(ref, "ref")

            l_data["dct_references_s"] = '{' + (','.join(ref)) + '}'
            print("----------")

        # map child date to stub record
        l_data=self.map_data(_l,l_data);
        # update the id
        l_data["id"] = _l.resource_id+"-"+str(r.end_point.id)
        l_data["dct_identifier_sm"] = _l.resource_id+"-"+str(r.end_point.id)

        # todo assign the geometry type?

        # add attribute information
        try:
            if _l.layer_json and 'fields' in _l.layer_json and 'type' in _l.layer_json["fields"][0]:
                l_data["fields"] = _l.layer_json["fields"]
        except:
            pass

        # add preset drawing details
        # note: these are stored in the layer_json if they are present

        if _l.layer_json and 'drawingInfo' in _l.layer_json:
            l_data["drawing_info"] = _l.layer_json["drawingInfo"]

        if hasattr(_l, 'geometry_type') and hasattr(_l.geometry_type, 'name'):
            l_data["gbl_resourceType_sm"] = self.get_geom_type(_l.geometry_type.name)

        if hasattr(_l, 'format') and hasattr(_l.format, 'name'):
            l_data["dct_format_s"] = self.get_format_type(_l.format.name)

        if hasattr(_l, 'name'):
            l_data["dct_title_s"] = _l.name
        if hasattr(_l, 'title'):
            l_data["dct_title_s"] = _l.title



        #

        # take the parent url and store it along with the layer to allow full path url for map layer loaded

        # extract the urls from the parent
        # todo we should have separate urls (featureserver, metadata, download, etc) for each layer
        if not is_child_record:

            layer_ref = self.get_resource_urls(_l,r)
            if self.verbosity > 1:
                print(layer_ref, "layer_ref")
            if layer_ref is not None:
                l_data["dct_references_s"] = '{' + (','.join(layer_ref)) + '}'

        # get a more accurate bounds for the layer

        if hasattr(_l, "bounding_box") and hasattr(_l.bounding_box,'extent'):
            l_data["dcat_bbox"] = self.get_bounds(_l.bounding_box)
            # lets also save a polygon representing the points for image overlays.
            l_data["locn_geometry"] = self.get_poly(_l.bounding_box)


        # todo add child specific descriptions

        # when there are more than 1 children - suppress the records and store with parent
        if not is_parent:
            l_data["solr_type"] = "child"
            # l_data["path"] = r.resource_id + ".layer"
            l_data["gbl_suppressed_b"] = False #True
            #store a direct reference to the parent
            l_data["dct_isPartOf_sm"] = r.resource_id

        # Add the date
        date_str_fmt = "%Y-%m-%dT%H:%M:%SZ"
        if _l.created is not None:
            l_data["dct_issued_s"] = _l.created.strftime(date_str_fmt)
        if _l.modified is not None:
            l_data["dct_issued_s"] = _l.modified.strftime(date_str_fmt)

        print("And the date is....", l_data["dct_issued_s"],r.modified)

        return l_data


    def get_resource_urls(self,l,r):
        layer_ref = []
        for u in r.url_set.all():

            layer_ref.append(self.match_ref(u.url, u))

            # url_type = str(u.url_type)
        # if str(l["type"]) != "Raster Layer":
        #     opt_id = "/" + str(l["id"])
        #
        #     # layer_ref.append(self.match_ref(u.url + opt_id, str(l["type"])))
        #     layer_ref.append(self.match_ref(u.url + opt_id, u))
        # elif url_type == "info_page":
        #     # todo - figure out when we can direct users to + "/" +
        #     # looks like ?layer=id if more appropriate
        #     url = u.url + "?layer=" + str(l["id"])
        #     layer_ref.append(self.match_ref(url, url_type))
        #
        #     # create Download urls
        #     # todo - link these to available options
        #
        #     d_url = u.url + "_" + str(l["id"])
        #     print("get download urls!!!!")
        #     layer_ref.append(self.match_ref(
        #         "[" + ','.join([d_url + ".zip", d_url + ".csv", d_url + ".kml", d_url + ".geojson"]) + "]",
        #         "Download"))
        #
        # elif url_type == "metadata":
        #     url = u.url + "&layer=" + str(l["id"])
        #     layer_ref.append(self.match_ref(url, url_type))

        print('layer_ref',layer_ref)
        return layer_ref

    ###
    def get_bounds(self,_bounds):
        ex = list(map(str, _bounds.extent))  # lower left and upper right coordinates as string

        # p_data["locn_geometry"] = "ENVELOPE(" + west + "," + east + "," + north + "," + south + ")"
        return "ENVELOPE(" + ex[0] + "," + ex[2] + "," + ex[3] + "," + ex[1] + ")"

    def get_poly(self,_bounds):

        points=[]
        for b in _bounds:
            for p in b:
                points.append(str(p[0])+" "+str(p[1]))
        return "POLYGON(("+','.join(points)+"))"

    def get_geom_type(self,_type):
        if _type==None:
            print("No type indicated")
            return ""

        print("get_geom_type", _type)
        # return a standard type based on lookup table
        # Raster,Polygon,Line,Image, Point, Mixed,MultiPolygon,MultiLineString, MultiPoint,Paper Map,Collection
        # match  key:
        _type = _type.lower()
        if _type.find('polygon')>-1:
            return 'Polygon'
        if _type.find('line')>-1:
            return 'Line'
        if _type.find('point')>-1:
            return 'Point'
        if _type.find('raster')>-1:
            return 'Raster'
        else :
            return _type


    def get_format_type(self,_type):
        type_value={"csv":"CSV",
                    "shapefile": "Shapefile",
                    "sqlite": "SQLite Database",
                    "gpkg": "",
                    "filegdb": "File Geodatabase",
                    "featureCollection": "",
                    "geojson": "GeoJSON",
                    "excel": "Excel",
                    "geotiff": "GeoTIFF",
                    "jpeg": "JPEG",
                    "tiff": "TIFF",
                    "raster": "Raster Dataset",
                    "scan": "Scanned Map",
                    }
         # ArcGRID, Paper Map, , E00 Cartographic Material, ESRI Geodatabase, , , ,

        #match key:
        type = _type.lower()
        if type in type_value:
            return type_value[type]
        elif _type == None:
            return ""
        else:
            return _type


    def get_refs(self,urls,_type):
        refs=[]
        downloads=[]
        print("get REFS *")
        for u in urls:
            type = str(u.url_type.name).lower()

            # if type == "base_url" and _type:
            #     # substitute the layer type for this
            #     type=_type

            # # todo - this should be set via harvest or at least in the admin
            # if str(u.url_type) == "base_url" and "iiif" in u.url:
            #     type = "iiif"

            ref = self.match_ref(u.url, u.url_type)
            if ref:
                if type =="download":
                    # check for another download

                    download_str= '"url":"'+u.url+'"'
                    if u.url_label:
                          download_str+=',"label":"' + u.url_label.name+'"'

                    downloads.append("{"+download_str+"}")
                else:
                    refs.append(ref)
            else:
                if self.verbosity > 1:
                    print(" not supported yet for type:",u.url_type,_type)

        # check for download
        if len(downloads)>0:


             # if there is more than 1 download URL - group them
             if len(downloads)>1:
                 download_str = "["+",".join(downloads)+"]"
             else:
                 # rely on the download string
                 download_str = "["+downloads[0]+"]"
                 print('download_str', download_str)
             refs.append('"http://schema.org/downloadUrl":' + download_str )

        return refs


    def match_ref(self, val,u_obj):

        if self.verbosity>1:
            print("match_ref ",val,u_obj)
        if u_obj.ref:
            return '"'+u_obj.ref+'":"' + val + '"'
        else:
            return