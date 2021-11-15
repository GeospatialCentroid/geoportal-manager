"""
The subclass class FileParser_CDM looks through the loaded dSPACE record data and extracts the relevant information for db insert
"""
# TODO: this class needs to be updated to use the change management system

from .FileParser import FileParser

class FileParser_DS(FileParser):
    def __init__(self,props):
        for p in props:
            setattr(self,p, props[p])

        super(FileParser_DS, self).__init__(props)

    def create_record(self, r, child_obj=False,open_prefix=False):

        '''
        look though the metadata and create a record for each item
        Be sure to distinguish between a parent record vs a child record
        child records have
            a parent id

        :param r:
        :return: the modified result for use in assignment to the child record
        '''

        if open_prefix:
            self.open_prefix = open_prefix

        # Because each record could have many layers association with it we need to check for this

        # create new dict for each and assign the remapped values

        resource = dict(r)

        # setup lists
        resource["places"]=[]
        resource['categories'] = []

        resource["description"] = ""
        resource["format"] = ""

        # get all the metadata
        for f in child_obj['metadata']:
            # either store in a list
            if f['key'] == "dc.coverage.spatial":
                resource["places"].append(f['value'])
            elif f['key'] == "dc.format.medium" and f['value']=="historical maps":
                resource["categories"].append("historic")
            elif f['key'] == "dc.description":
                resource["description"] += f['value'] + " "
            else:
                # else store with the object
                resource[f['key']] = f['value']

        # generate links for all the items
        resource["urls"] = []
        # get all the bitstreams - links
        for f in child_obj['bitstreams']:
            if(f["bundleName"]== "THUMBNAIL"):
                resource["thumb"] = self.open_prefix + f["retrieveLink"]
            elif (f["bundleName"] == "ORIGINAL"):
                resource["urls"].append({'url_type': "download", 'url': self.open_prefix + f["retrieveLink"]})
                resource["format"] = f["format"]
        #     todo something with - "bundleName": "TEXT"

        if "dc.identifier.uri" in resource:
            resource["urls"].append({'url_type': "info_page", 'url': resource["dc.identifier.uri"]})

        return resource