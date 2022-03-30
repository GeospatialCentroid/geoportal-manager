"""
The subclass class FileParser_CDM looks through the loaded CONTENTdm record data and extracts the relevant information for db insert
"""

import re
from .FileParser import FileParser

class FileParser_CDM(FileParser):
    def __init__(self,props):
        for p in props:
            setattr(self,p, props[p])

        super(FileParser_CDM, self).__init__(props)

    def create_record(self, r, child_obj=False, open_prefix=False):
        if open_prefix:
            self.open_prefix = open_prefix
        '''
        look though the metadata and create a record for each item
        Be sure to distinguish between a parent record vs a child record
        child records have
            a parent id

        :param r:
        :return: the modified result for use in assignment to the child record
        '''
        # Because each record could have many layers association with it we need to check for this

        # create new dict for each and assign the remapped values

        if r is not None:
            resource = dict(r)
        else:
            resource = dict(child_obj)

        #
        for f in child_obj['fields']:
            resource[f['key']] = f['value']

        #todo
        #break-up 'subjec' and form key words e.g Fort Collins (Colo.)--Aerial views; Larimer County (Colo.)--Maps, Topographic;",
        # break-up "geogra",
        # "value": "LarimerCounty",


        # generate links using both parent and child details
        #"thumbnailUri": "/api/singleitem/collection/hm/id/1434/thumbnail",
        resource["thumb"] = self.open_prefix + resource["thumbnailUri"]

        resource["name"]=''

        ####
        if "id" not in resource and child_obj:
            resource['id'] = child_obj['thumbnailUri'][
                        child_obj['thumbnailUri'].index("/id/") + 4:child_obj['thumbnailUri'].index("/thumbnail")]

        if 'identi' in resource:
            resource['id'] = resource['identi']
            
        print("the id is...", resource['id'])


        # only a parent will have these
        if "creato" in resource:
            resource['owner'] = resource['creato']
        else:
            resource['owner'] = 'Unknown'

        if "langua" in resource:
            resource["language"] = resource['langua']

        if "publis" in resource:
            resource['publisher'] = resource['publis']

        if "descri" in resource:
            resource['description'] = resource['descri']
        else:
            resource['description'] = ''

        if "righta" in resource:
            resource['accessInformation'] = resource['righta']
        else:
            resource['accessInformation'] = ""

        if "rights" in resource:
            resource['licenseInfo'] = resource['rights']
        else:
            resource['licenseInfo'] = ""

        if 'date' not in resource:
            if 'datea' in resource:
                resource['date'] = resource['datea']
            else:
                resource['date'] = None

        if resource['date'] is not None and not resource['date'].isdigit():
            try:
                regex = "\d{4}"
                match = re.findall(regex, resource['date'])
                if len(match) > 0:
                    for m in match:
                        if int(m) <= self.curr_year and int(m) > 1500:
                            resource['date'] = m
            except:
                resource['date'] = None

        resource['year'] =  resource['date']

        if resource['year'] and resource['year'].isdigit():
            resource['year']=int(resource['year'])

        if isinstance( resource['year'] , str):
            resource['year']=None

        #########
        
        resource["urls"] = []
        # strip the head and the tail from the 'itemLink' to make an information e.g "/{single or com}/collection/hm/id/1275"
        # https://fchc.contentdm.oclc.org/digital/collection/hm/id/1275
        resource["info_page"] = self.open_prefix + resource["thumbnailUri"][resource["thumbnailUri"].index("/collection"):resource["thumbnailUri"].index("/thumbnail")]
        print(resource["info_page"], "------info_page")
        resource["urls"].append({'url_type': "info_page", 'url': resource["info_page"]})

        resource["urls"].append({'url_type': "download", 'url': self.open_prefix + child_obj["downloadUri"]})




        # iiifInfoUri not available for pdfs
        # "filetype": "cpd",
        # for consistency use the higher level variable 'filetype'
        if 'filetype' not in resource:
            resource['filetype'] = resource['contentType']
            if resource['filetype']=='application/pdf':
               resource['filetype']="cpd"
               resource["format"] = "PDF"

        if resource['filetype'] != "cpd":
            url=child_obj["iiifInfoUri"]
            if not url.startswith("http"):
                url = self.open_prefix + url
            resource["urls"].append({'url_type': "iiif", 'url': url })
            resource["type"] = "iiif"
            resource["format"] = "JPEG"

        resource["geometry_type"] = "Raster"


        # if resource['filetype'] != "cpd" or r==None:
        #     # singleitems have images - parents do not - we have 3 cases - upper level no children and children have images
        #     # todo - investigate further about image for compound files - current just support jp2 and tif
        #     # e.g https://fchc.contentdm.oclc.org/digital/api/singleitem/image/pdf/hm/1404/default.png
        #     # we have https://fchc.contentdm.oclc.org/digital/api/singleitem/image/hm/1434/default.jpg
        #     # for compound artifacts we need to load the child information
        #     # take the 'objectInfo'>'page' items and the 'pageptr' id. Append this to current url address
        #     # https://fchc.contentdm.oclc.org/digital/api/singleitem/collection/hm/id/1405

        url = child_obj["imageUri"]
        if not url.startswith("http"):
            url = self.open_prefix + url
        resource["urls"].append({'url_type': "image", 'url': url})

        if "iiifInfoUri" in child_obj:
            url = child_obj["iiifInfoUri"]
            if not url.startswith("http"):
                url = self.open_prefix + url
            resource["urls"].append({'url_type': "iiif", 'url': url})



        # print(*resource["urls"])

        return resource