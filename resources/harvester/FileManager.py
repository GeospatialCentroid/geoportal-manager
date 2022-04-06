"""
The FileManager class is used to handle how each endpoint type is treated.
"""

import os.path
from os import path


from .FileCollection_AGO import FileCollection_AGO
# from .FileParser_AGO import FileParser_AGO

from .FileCollection_CDM import FileCollection_CDM
from .FileParser_CDM import FileParser_CDM

from .FileCollection_DS import FileCollection_DS
from .FileParser_DS import FileParser_DS

from .FileCollection_DCAT import FileCollection_DCAT
from .FileParser_ARC import FileParser_ARC

from .FileCollection_CO import FileCollection_CO


class FileManager:
    '''
    Keep track of all the files to be downloaded.
    There are many, since only 100 responses can be downloaded at a time
    '''
    def __init__(self,props):
        for p in props:
            setattr(self,p, props[p])


    def load(self,props):
        # create the storage folder if it doesn't exists
        if not path.exists(self.path + self.data_folder):
            os.mkdir(self.path + self.data_folder)

        parse_props={
                "categories": self.categories,
                "places": self.places,
                "file_manager": self,
        }

        if props["end_point_type"] =='c':
            #  we're dealing with contentDM
            fileParser = FileParser_CDM(parse_props)
            # add the file_parser to the collection which should start the process
            props["file_parser"] = fileParser
            file_collection = FileCollection_CDM(props)
        elif props["end_point_type"] == 'ds':
            # create a parsing file and load in the categories
            fileParser = FileParser_DS(parse_props)
            props["file_parser"] = fileParser
            file_collection = FileCollection_DS(props)
        elif props["end_point_type"] == 'a':
            # create a parsing file and load in the categories
            # fileParser = FileParser_AGO(parse_props)
            #use the same parser as DCAT
            fileParser = FileParser_ARC(parse_props)
            props["file_parser"] = fileParser
            file_collection = FileCollection_AGO(props)
        elif props["end_point_type"] == 'd':
            # dcat
            fileParser = FileParser_ARC(parse_props)
            props["file_parser"] = fileParser
            file_collection = FileCollection_DCAT(props)
        elif props["end_point_type"] == 'co':
            fileParser = FileParser_ARC(parse_props)
            props["file_parser"] = fileParser
            file_collection = FileCollection_CO(props)

        else:
            print("No support yet for: ", props["end_point_type"],"?@!" )

        return file_collection


