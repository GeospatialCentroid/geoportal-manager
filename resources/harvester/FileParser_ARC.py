"""
The subclass class FileParser_ARC looks through the loaded ArcGIS record data and extracts the relevant information for db insert
"""

from datetime import datetime
from .. import utils


from .FileParser import FileParser

class FileParser_ARC(FileParser):
    def __init__(self,props):
        print("FileParser_ARC init!")
        for p in props:
            setattr(self,p, props[p])

        super(FileParser_ARC, self).__init__(props)

    def create_record(self, _r, child_obj=False, file_collection=False):
        '''
        look though the metadata and create a record for each item

        :param r:
        :return: the modified result for use in assignment to the child record
        '''

        # create new dict for each and assign the remapped values
        # for k in _r:
        #     print("_r",k)

        _r = dict(_r)


        if _r and not child_obj:
            resource = _r
            resource["geometry_type"] = ""
            resource["format"] = ""
        else:
            resource = dict(child_obj)
            # put variables in common place
            if 'keyword' in resource:
                resource['tags'] =  resource['keyword']

            if 'identifier' in resource:

                resource['id'] = resource['identifier']
                if "/" in resource['id']:
                    resource['id'] = resource['identifier'][resource['identifier'].rindex('/') + 1:]

            if 'contactPoint' in resource:
                resource['owner'] = resource['contactPoint']['fn']

            if 'license' in resource:
                resource['licenseInfo'] = resource['license']
            else:
                resource['licenseInfo'] = None

            if 'issued' in resource:
                resource['created'] = resource['issued']

            if 'editingInfo' in resource:
                resource['modified'] = datetime.utcfromtimestamp(resource['editingInfo']['lastEditDate']/ 1000)

            resource['name'] = None
            resource['thumb'] = None
            resource['accessInformation'] = None

            # this one is particularly tricky to pin down
            # need to distinguish between type and format
            # data type or geometry types
            resource["geometry_type"] = ""
            resource["format"] = ""
            resource["type"] = ""

        if "geometryType" in _r and _r["geometryType"] is not None and _r["geometryType"] != "":
            resource["geometry_type"] = _r["geometryType"]


        # make the type available even when nested
        if child_obj and "type" in child_obj:
            _r["type"] = child_obj["type"]

        if "type" in _r:
            resource["type"] = _r["type"]
            if resource["type"].lower().find("feature") > -1 and resource["format"]=="":
                resource["geometry_type"] = "Vector"
                resource["format"] = "Shapefile"
            elif resource["type"].lower().find("raster") > -1:
                resource["geometry_type"] = "Raster"
                resource["format"] = "Raster Dataset"


        if "supportedExportFormats" in _r:
            formats=_r["supportedExportFormats"].split(",")
            for f in ["shapefile", "sqlite", "gpkg", "filegdb", "featureCollection", "geojson", "csv", "excel"]:
                if f in formats:
                    resource["format"] = f
                    break



        # try to get the year
        resource["year"] = self.get_year(resource)

        if "description" in resource and resource["description"] == "" and "snippet" in resource:
            resource["description"]=resource["snippet"]



        if _r and not child_obj:
            # update the parent time stamp for saving
            if 'created' in resource:
                resource['created'] = datetime.utcfromtimestamp(resource['created'] / 1000)
                resource['modified'] = datetime.utcfromtimestamp(resource['modified'] / 1000)

        # result doc: https://developers.arcgis.com/rest/users-groups-and-items/search.htm

        resource["bounding_box"] = None
        # reformat extent
        extent=None
        spatial_reference = False



        if 'extent' in resource:
            extent = resource["extent"]

        if "spatialReference" in resource:
            spatial_reference = resource["spatialReference"]

        if 'fullExtent' in resource:
            extent = resource["fullExtent"]
            if "spatialReference" in extent:
                spatial_reference = extent["spatialReference"]

        if extent:
            resource["bounding_box"] = utils.get_extent(extent,spatial_reference)

        if 'spatial' in resource:
            resource["bounding_box"]=resource["spatial"].split(",")


        # add some modified values
        # todo keep track of whether we added new pieces of information
        # this will be captured in the database

        resource["categories"] = self.get_categories(resource)
        print ("get categories ----------- ", resource["categories"])
        resource["places"] = self.get_places(resource)

        # print(resource["places"])

        # store the urls for easy access
        resource["urls"] = []
        if _r and not child_obj and 'id' in resource:
            # generate a link to the landing page - only do this on parent objects
            resource["info_page"] = file_collection.open_prefix + str(resource['id'])
            resource["urls"].append({'url_type': "info_page", 'url': resource["info_page"]})
            if "thumbnail" in resource:
                resource["thumb"] = file_collection.arc_item_prefix + str(resource['id']) + "/info/" + resource["thumbnail"]
            else:
                resource["thumb"] = None

            # not all layers will have the following - need a way to check these
            resource["metadata"] = file_collection.arc_item_prefix + str(resource['id']) + "/info/metadata/metadata.xml?format=default"
            resource["urls"].append({'url_type': "metadata", 'url': resource["metadata"]})

            #store the web service
            if "url" in resource:
                url =resource["url"]
                if resource["type"].lower().find("feature")>-1:
                    url+="/0/"
                resource["urls"].append({'url_type': resource["type"].lower(), 'url': url})
        else:
            # we are working with a child object which has all the urls
            if "landingPage" in resource:
                resource["info_page"] = resource['landingPage']

            # loop over the distributions
            if "distribution" in resource:
                for d in resource['distribution']:
                    url =d["accessURL"]
                    # quick fix for broken ESRI DCAT urls
                    url=url.replace("/maps/","/datasets/")
                    if d["title"] in file_collection.api_types:
                        # store the base url
                        r_type = resource["type"].lower()
                        if r_type == "raster layer":
                            r_type = "mapservice"
                        resource["urls"].append({'url_type': r_type, 'url': url})
                        # # set the type while we're at it
                        # resource["type"] = "Dataset|Service"
                    elif "mediaType" in d and d["mediaType"] == "text/html":
                        resource["urls"].append({'url_type': "info_page", 'url': url})
                    elif d["title"]:
                        resource["urls"].append({'url_type': "download", 'url': url, 'label': d["title"]})
                    else:
                        resource["urls"].append({'url_type': "html", 'url': url})



        #  only for parent records
        if "type" in resource and _r:
            if resource["type"] not in ["Raster Layer", "StoryMap", "Web Mapping Application"]:
                # it should also be noted that the zip download links return json with a 'serviceUrl' which actually links to the data
                # todo add all the download links associated with each layer
                # start with the first one
                resource["download"] = file_collection.open_prefix + str(resource['id']) + "_0" + ".zip"
                resource["csv"] = file_collection.open_prefix + str(resource['id']) + ".csv"

                # print("DOWNLOAD", resource["download"])

            if resource["type"] in ["StoryMap", "Web Mapping Application"]:
                resource["info_page"] = resource["url"]


        if isinstance(resource['bounding_box'], list):
            # for simplicity - save the bounding_box as a polygon
            b = [str(x) for x in resource["bounding_box"]]
            try:
                resource["polygon"] = b[0] + " " + b[1] + ", " + b[0] + " " + b[3] + ", " + b[2] + " " + b[3] + ", " + b[
                    2] + " " + b[1] + ", " + b[0] + " " + b[1]
            except:
                resource["polygon"]=None;
            resource["bounding_box"] = ','.join([str(x) for x in resource["bounding_box"]])

        return resource