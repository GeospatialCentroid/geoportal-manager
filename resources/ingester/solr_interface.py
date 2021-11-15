#original

import pysolr
import json

class SolrInterface(object):

    def __init__(self, log=None, url=None):
        self.solr_url = url
        self.log = log
        self.solr = self._connect_to_solr()

    def _connect_to_solr(self):
        """
        Connects to Solr using the url provided when object was instantiated.
        """
        print("connecting to",self.solr_url)
        return pysolr.Solr(self.solr_url,always_commit=True)

    def escape_query(self, raw_query):
        """
        Escape single quotes in value.
        """
        return raw_query.replace("'", "\'")

    def delete_everything(self):
        print("delete_everything...Yicks - should ask if you really really want to delete everything!!!")
        resp = self.solr.delete(q='*:*')
        print(resp)

    def delete_query(self, query):
        resp = self.solr.delete(q=self.escape_query(query))
        print(resp)

    def json_to_dict(self, json_doc):
        j = json.load(open(json_doc, "r"))
        return j

    def add_json_to_solr(self, json_doc):
        record_dict = self.json_to_dict(json_doc)
        self.add_dict_to_solr(record_dict)


    def add_dict_list_to_solr(self, list_of_dicts):
        # status 0 means success
        print("Adding {} items".format(len(list_of_dicts)))
        try:
            resp = self.solr.add(list_of_dicts)
            print(resp)
        except pysolr.SolrError as e:
            print("Solr Error: {e}".format(e=e))

    def search(self,query):
       return self.solr.search(self.escape_query(query))