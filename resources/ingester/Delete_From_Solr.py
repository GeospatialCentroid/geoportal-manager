#
#
#

#! /usr/bin/env python
import sys
from collections import OrderedDict
import argparse


# local imports
from .solr_interface import SolrInterface
from django.conf import settings

log = False

class Delete_From_Solr(object):

    def __init__(self, props):

        self.interface = CSWToGeoBlacklight(settings.SOLR_URL, settings.SOLR_USERNAME, settings.SOLR_PASSWORD)
        # interface.delete_everything("")


class CSWToGeoBlacklight(object):

    def __init__(self, SOLR_URL, SOLR_USERNAME, SOLR_PASSWORD, INST=None,
                 max_records=None, COLLECTION=None, CODE=None, UUID=None, PUBLISHER=None, SUBJECT=None):

        if SOLR_USERNAME and SOLR_PASSWORD:
            SOLR_URL = SOLR_URL.format(
                username=SOLR_USERNAME,
                password=SOLR_PASSWORD
            )
        self.solr = SolrInterface(log=log, url=SOLR_URL)

        self.inst = INST
        self.records = OrderedDict()
        self.record_dicts = OrderedDict()
        self.max_records = max_records
        self.uuid = UUID

        if COLLECTION:
            self.collection = '"' + COLLECTION + '"'
        else:
            self.collection = None


        self.institutions_test = {
            "minn": '"Minnesota"'
        }
        self.institutions = {
            "": '""',
        }

        self.identifier = {
            "rec": '"99-0001-noIdentifier"'

        }
        self.publisher = {
            "": '""'
        }

        self.subject = {
            "del": '"DELETE"'

        }

        self.code = {

        }

        self.collection = {

        }
    ###

    def delete_everything(self, uuid):
        self.solr.delete_everything()

    def delete_records_institution(self, inst):
        """
        Delete records from Solr.

        """
        self.solr.delete_query("dct_provenance_s:" + self.institutions[inst])

    def delete_one_record(self, uuid):
    	self.solr.delete_query("layer_slug_s:" + uuid)

    def delete_records_collection(self, collection):
        """
        Delete records from Solr.
        """
        self.solr.delete_query("dct_isPartOf_sm:" + self.collection[collection])

    def delete_records_code(self, code):
        """
        Delete records from Solr.
        """
        self.solr.delete_query("b1g_code_s:" + self.code[code])

    def delete_records_publisher(self, publisher):
        """
        Delete records from Solr.
        """
        self.solr.delete_query("dc_publisher_sm:" + self.publisher[publisher])

    def delete_records_subject(self, subject):
        """
        Delete records from Solr.
        """
        self.solr.delete_query("dc_subject_sm:" + self.subject[subject])


    def update_one_record(self, uuid):
        url = self.CSW_URL.format(virtual_csw_name="publication")
        self.connect_to_csw(url)
        self.csw_i.getrecordbyid(
            id=[uuid],
            outputschema="http://www.isotc211.org/2005/gmd"
        )
        self.records.update(self.csw_i.records)
        rec = self.records[uuid].xml
        rec = rec.replace("\n", "")
        root = etree.fromstring(rec)
        record_etree = etree.ElementTree(root)
        inst = self.get_inst_for_record(uuid)
        result = self.transform(
            record_etree,
            institution=self.institutions[inst]
        )
        result_u = unicode(result)

        self.handle_transformed_records()

    @staticmethod
    def chunker(seq, size):
        if sys.version_info.major == 3:
            return (seq[pos:pos + size] for pos in range(0, len(seq), size))
        elif sys.version_info.major == 2:
            return (seq[pos:pos + size] for pos in xrange(0, len(seq), size))

    def handle_transformed_records(self, output_path="./output"):

        if self.to_csv:
            self.to_spreadsheet(self.record_dicts)

        elif self.to_json:
            self.output_json(output_path)

        elif self.to_xml:
            self.output_xml(output_path)

        elif self.to_xmls:
            self.single_xml(output_path)

        elif self.to_opengeometadata:
            self.output_json(self.to_opengeometadata)
            self.output_xml(self.to_opengeometadata)
            self.output_layers_json(self.to_opengeometadata)

        else:
            self.solr.add_dict_list_to_solr(self.record_dicts.values())



