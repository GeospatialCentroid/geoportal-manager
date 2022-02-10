"""
The super class FileCollection is used to handle json file loading/saving and database ingestion through Change Management System

"""

from resources.models import Resource, Format, Category,Owner,Publisher,Type, Language,Category,Tag,Place,URL,URL_Type,URL_Label,Geometry_Type,Change_Log

from django.contrib.gis.geos import GEOSGeometry

import urllib.request, json
import ssl
import os.path
from os import path

from datetime import datetime

from bs4 import BeautifulSoup


class FileCollection:
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
        self.folder = self.org_name+self.date

        if not path.exists(self.path+self.folder):
            os.mkdir(self.path+self.folder)

        self.load_results()

    def load_file_call_func(self, _file, _url, _func, parent_obj=False):
        """

        :param _file: the name (w/ path) of the file to save
        :param _url: the absolute URL to the json
        :param _func: The function to call upon completion
        :param parent_obj: extra info to retain when loading
        :return: None
        """
        if not path.exists(_file) or self.overwrite:
            # setup the url to load each request
            print("loading file", _url)
            urllib.request.urlretrieve(_url, _file)
            try:
                context = ssl._create_unverified_context()
                response = urllib.request.urlopen(_url, context=context)
                with open(_file, 'w', encoding='utf-8') as outfile:
                    outfile.write(response.read().decode('utf-8'))
                self.load_file(_file, _func, parent_obj)

            except ssl.CertificateError as e:
                print("Data portal URL does not exist: " + _url)

        else:
            # load the file
            self.load_file(_file,_func, parent_obj)

    def load_file(self,_file, _func, parent_obj=False):
        """

        :param _file: : The name (w/ path) of the file to save - relayed from "load_file_call_func"
        :param _func: _func: The function to call upon completion - relayed from "load_file_call_func"
        :param parent_obj: Extra info to retain when loading - relayed from "load_file_call_func"
        :return: None
        """
        try:
            _json = self.open_json(_file)
        except:

            _json = self.parse_json(_file)

        getattr(self, _func)(_json, parent_obj)

    def open_json(self,_file):
        """

        :param _file: The name (w/ path) of the local file to open
        :return: interprets text as JSON
        """
        try:
            outfile = open(_file)
            _json = json.load(outfile)
            outfile.close()
            return _json
        except:
            raise


    def parse_json(self,_file):
        """
        Extracts the JSON form malformed file
        :param _file: The name (w/ path) of the local file to open
        :return: A JSON file
        """
        outfile = open(_file)
        s = outfile.read()
        _json = s[s.find("(") + 1:s.rfind(")")]
        outfile.close()
        return json.loads(_json)

    def convert_date_to_db_format(self,date_str):
        """
        Takes a date string and converts it to a date object
        :param data_str: The date string - could be either str, int or date object
        :return: the date object
        """
        db_format = '%Y-%m-%d %H:%M:%S+00:00'
        if isinstance(date_str, int) :
            if len(str(date_str))==8:
                return datetime.strptime(str(date_str), '%Y%m%d').strftime(db_format)
            return datetime.fromtimestamp(date_str/1000.0)


        if isinstance(date_str, str):
            return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S.000Z').strftime(db_format)
        else:
            return date_str.strftime(db_format)

    def save_record(self, obj, raw_json, layer_json=None, parent_resource=None):
        """

        :param obj: The dict with all the values
        :param raw_json: The json string to save in the raw_json slot
        :param layer_json: The json string to save in the layer_json slot
        :param parent_resource: For saving the parent ID as part of the child record when appropriate
        :return: The saved database record
        """
        owner=None
        if 'owner' in obj:
            owner, created = Owner.objects.get_or_create(name=obj['owner'])

        type = None
        if 'type' in obj:
            type, created = Type.objects.get_or_create(name=obj['type'])

        geometry_type = None
        if 'geometry_type' in obj and obj['geometry_type'] is not None:
            geometry_type, created = Geometry_Type.objects.get_or_create(name=obj['geometry_type'])

        format = None
        if 'format' in obj:
            format, created = Format.objects.get_or_create(name=obj['format'])

        publisher = None
        # replace the json publisher obj with the name string
        if 'publisher' in obj and 'name' in obj['publisher']:
            obj['publisher']= obj['publisher']['name']
        if 'publisher' in obj:
            publisher, created = Publisher.objects.get_or_create(name=obj['publisher'])

        if 'polygon' in obj and obj['polygon'] is not None:
            # todo make 'srid' dynamic
            obj['polygon'] = GEOSGeometry("POLYGON((" + obj['polygon'] + "))",
                            srid=4326)
        else:
            obj['polygon']=None

        # to aligned metadata and database dates - reformat the date before ingest
        if 'created' in obj:
            obj['created'] = self.convert_date_to_db_format(obj['created'])
        else:
            obj['created']=None

        if 'modified' in obj:
            obj['modified'] = self.convert_date_to_db_format(obj['modified'])
        else:
            obj['modified'] = None

        if 'year' in obj and obj['year'] !=None and obj['year'] !='':
            obj['year'] = int(obj['year'])
        else:
            obj['year'] =None


        data_struct = {"resource_id": obj['id'],
                       "end_point": self.end_point,
                       "title": obj['title'],
                       "alt_title": obj['name'],
                       "description": obj['description'],

                       "bounding_box": obj['polygon'],
                       "year": obj['year'],
                       "thumbnail": obj['thumb'],
                       "license_info": obj['licenseInfo'],
                       "access_information": obj['accessInformation'],
                       "geometry_type": geometry_type,
                       "format": format,
                       "type": type,
                       "harvest": self.harvest,

                       "raw_json": raw_json,
                       "layer_json": layer_json,
                       "created": obj['created'],
                       "modified": obj['modified'],
                       "accessioned": datetime.now().strftime("%Y-%m-%d %H:%M:%S+00:00"),  # to remove the milliseconds
                       "parent": parent_resource}

        try:
            r = Resource.objects.get(resource_id=obj['id'], end_point=self.end_point)
            # prevent overwriting manual edits

            # get all the changes
            changes = Change_Log.objects.filter(resource_id=r.id).order_by('-date')
            #
            distict = []
            latest_changes = []
            for c in changes:
                if c.field_name not in distict:
                    distict.append(c.field_name)
                    latest_changes.append(c)

            for d in data_struct:
                # update all the values that have changed
                # exclude fields from change log
                exclude_field = ["harvest", "accessioned"]
                if str(getattr(r, d)) != str(data_struct[d]) and d not in exclude_field:
                    # print("compare", d, getattr(r, d), "vs", data_struct[d])
                    # make sure we're not over writing a user entered change
                    has_manual_change = False
                    for c in latest_changes:
                        if c.field_name == d and c.change_type == 'u':
                            has_manual_change = True
                    if not has_manual_change:
                        setattr(r, d, data_struct[d])
            r.save()
            print("Already exists!!! But Updated")
        except Resource.DoesNotExist:
            print("Create a new resource!!!")
            r = Resource.objects.get_or_create(**data_struct)[0]

            if owner:
                r.owner.add(owner)

        if publisher:
            # use the metadata publisher if available
            r.publisher.add(publisher)
            pass
        else:
            r.publisher.add(self.publisher)

        if 'language' in obj:
            r.languages.add(Language.objects.get_or_create(name=obj['language'])[0])
        # create the many to many objects then add them to the resource
        if 'categories' in obj:
            for c in obj['categories']:
                r.category.add(Category.objects.get_or_create(name=c)[0])
        if 'tags' in obj:
            for t in obj['tags']:
                r.tag.add(Tag.objects.get_or_create(name=t)[0])
        if 'places' in obj:
            for p in obj['places']:
                # note the place is unique on two columns so use both to avoid duplicates
                ps = p.split("|")
                r.place.add(Place.objects.get_or_create(name=ps[0], name_lsad=ps[1])[0])

        # and lastly - create the urls  by looping over the ones in the resources
        for u in obj['urls']:
            print("Create the url type:", u)
            #  create the url type
            u_t, _ = URL_Type.objects.get_or_create(name=u['url_type'])

            # add url
            if not 'label' in u or u['label'] == None:
                u_l = None
            else:
                u_l, _ = URL_Label.objects.get_or_create(name=u['label'])

            try:
                URL.objects.get_or_create(url_type=u_t, url=u['url'], url_label=u_l, resource=r)
            except Exception as e:
                # print("Except",str(e))
                pass
        return r


    def convert_urls(self,html, prefix):
        """
        takes a string and looks for hrefs, for those found if the url is relative, make it absolute by adding the prefix
        :param html:
        :param prefix
        :return:
        """

        soup = BeautifulSoup(html, "lxml")
        for a in soup.findAll('a'):
            print("found url", a['href'])
            if not a['href'].startswith("http"):
                print("replace",prefix+a['href'])
                a['href'] = prefix+a['href']
                a.replace_with(a)


        return str(soup)