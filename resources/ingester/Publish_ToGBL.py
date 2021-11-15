#This script will add geoblacklight json files to Solr from a folder of nested files.
#check configSolr to change from dev to public server

import os
import sys
# from collections import OrderedDict
import argparse
import logging
import fnmatch

# to investigate inner workings

# # non-standard libraries.
# from lxml import etree
# # from owslib import csw
# from owslib.etree import etree
# from owslib import util
# from owslib.namespaces import Namespaces
# # import unicodecsv as csv
# # demjson provides better error messages than json
# import demjson
# import requests

# local imports
from .solr_interface import SolrInterface
from django.conf import settings

log = False

class Publish_ToGBL(object):

    def __init__(self, props):
        for p in props:
            setattr(self, p, props[p])

        interface = CSWToGeoBlacklight(settings.SOLR_URL, settings.SOLR_USERNAME, settings.SOLR_PASSWORD)

        interface.add_json(self.path)


# Catalogue Service for the Web (CSW)
class CSWToGeoBlacklight(object):

    def __init__(self, SOLR_URL, SOLR_USERNAME, SOLR_PASSWORD,
                 max_records=None):
        global log
        if SOLR_USERNAME and SOLR_PASSWORD:
            SOLR_URL = SOLR_URL.format(
                username=SOLR_USERNAME,
                password=SOLR_PASSWORD
            )

        self.solr = SolrInterface(log=log, url=SOLR_URL)


    def get_files_from_path(self, start_path, criteria="*"):
        files = []

        for path, folder, ffiles in os.walk(start_path):
            for i in fnmatch.filter(ffiles, criteria):
                files.append(os.path.join(path, i))
        return files

    def add_json(self, path_to_json):
        files = self.get_files_from_path(path_to_json, criteria="*.json")

        dicts = []

        for i in files:
            dicts.append(self.solr.json_to_dict(i))
        self.solr.add_dict_list_to_solr(dicts)


# def init_logger():
#     global log
#     if config.DEBUG:
#         log_level = logging.DEBUG
#     else:
#         log_level = logging.INFO
#     log = logging.getLogger('owslib')
#     log.setLevel(log_level)
#     ch = logging.StreamHandler(sys.stdout)
#     ch.setLevel(log_level)
#     log_formatter = logging.Formatter(
#         '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
#     )
#     ch.setFormatter(log_formatter)
#     log.addHandler(ch)

