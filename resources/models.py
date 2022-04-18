# from django.db import models

# Create your models here.

from django.contrib.gis.db import models
from django.core.validators import MaxValueValidator
from ckeditor.fields import RichTextField
from datetime import datetime
from django.forms.models import model_to_dict


class Harvest(models.Model):
    date = models.DateTimeField('Date harvested', null=True, blank=True)

    Trigger_Type = (
        ('s', 'schedule'),
        ('u', 'user')
    )
    trigger_type = models.CharField(max_length=1, choices=Trigger_Type)

    def __str__(self):
        return str(self.date)

class Language(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return str(self.name)

class Publisher(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return str(self.name)

class End_Point(models.Model):
    name = models.CharField(max_length=200)
    org_name = models.CharField(max_length=100)
    url = models.CharField(max_length=512)
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE,default=1)
    End_Point_Type = (
        ('d', 'dcat'),
        ('a', 'arc_gis_rest'),
        ('c', 'CONTENTdm'),
        ('ds', 'dspace'),
        ('co', 'codex')
    )
    end_point_type = models.CharField(max_length=2, choices=End_Point_Type, default='a')
    thumbnail = models.CharField(help_text="The URL to a static image of the publisher", max_length=512, null=True,
                                 blank=True)

    disclaimer = RichTextField(null=True, blank=True)
    def __str__(self):
        return str(self.name)

class Category(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=4)
    title = models.CharField(max_length=100)
    desc = models.CharField(max_length=500)
    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name_plural = "categories"

class Category_Keywords(models.Model):
    name = models.CharField(max_length=100, unique=True)
    category = models.ManyToManyField(Category)

    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name_plural = "category_keywords"


class Collection(models.Model):
    name = models.CharField(max_length=150, unique=True)
    keyword = models.ManyToManyField(Category_Keywords)
    def __str__(self):
        return str(self.name)

class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return str(self.name)

class Place(models.Model):
    name = models.CharField(max_length=100 )
    state_fp = models.CharField(max_length=100, default='')
    place_fp = models.CharField(max_length=100, default='')
    name_lsad = models.CharField(max_length=100, default='')

    class Meta:
        unique_together = (("name", "name_lsad"),)
    def __str__(self):
        return str(self.name)+", "+str(self.name_lsad)

class Named_Place(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return str(self.name)

class Type(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return str(self.name)

class Format(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return str(self.name)

class Geometry_Type(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return str(self.name)

class Resource_Type(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return str(self.name)

class Owner(models.Model):
    name = models.CharField(max_length=300, unique=True)
    full_name = models.CharField(max_length=500, null=True, blank=True)
    def __str__(self):
        return str(self.name)

class Resource(models.Model):
    '''

    [,"title","name", "description", # in database note: 'name' changed to alt_tile
     "languages", "owner", "publisher", "", # in database
     "categories", "tags", "created", "", "", "", "year",
     "places",
     "bounding_box", # in database
     "type", "Geometry Type", "type", "info_page", "download",
     "ms_url", "fs_url", "is_url","ts_url", "Slug", "publisher", "",# Code used in 'workflow' repo for assigning institution
     "", "", "Accrual Method", "Date Accessioned", "licenseInfo",
     "access", "", "","is_part_of","thumbnail"]
    '''
    id = models.AutoField(primary_key=True)
    resource_id = models.CharField(max_length=100)
    title= models.CharField(max_length=400)
    alt_title = models.CharField(max_length=200, null=True, blank=True)
    description = RichTextField(null=True, blank=True)
    bounding_box = models.PolygonField(null=True, blank=True)#,srid = 4326

    languages = models.ManyToManyField(Language, blank=True)
    owner = models.ManyToManyField(Owner, blank=True)
    publisher = models.ManyToManyField(Publisher, blank=True)
    category = models.ManyToManyField(Category, blank=True)
    collection = models.ManyToManyField(Collection, blank=True)
    tag = models.ManyToManyField(Tag, blank=True)

    created = models.DateTimeField('Date created', null=True, blank=True)
    modified = models.DateTimeField('Date modified', null=True, blank=True)
    accessioned = models.DateTimeField('Date accessioned', null=True, blank=True)

    year = models.IntegerField(null=True,blank=True, validators=[MaxValueValidator(9999)])
    temporal_coverage = models.CharField(help_text="The time period data collected or intended to represent. E.g '2001-2012'", max_length=500, null=True, blank=True)
    # place = models.ManyToManyField(Place, blank=True)
    named_place = models.ManyToManyField(Named_Place, blank=True)
    type = models.ForeignKey(Type, on_delete=models.SET_NULL,null=True, blank=True, help_text="The service type used to visualize the data in the browser")
    geometry_type = models.ForeignKey(Geometry_Type, on_delete=models.SET_NULL, null=True, blank=True, help_text="To differentiate between vector (Point, Line, Polygon), raster (Raster, Image), and nonspatial formats (table), or a combination (Mixed). Used as icon within interface")
    resource_type = models.ManyToManyField(Resource_Type, blank=True)
    format = models.ForeignKey(Format, on_delete=models.SET_NULL, null=True, blank=True, help_text="The format of the data. E.g Shapefile, GeoTIFF, JPEG, TIFF, ArcGRID, Paper Map, Geodatabase, E00 Cartographic Material, ESRI Geodatabase, SQLite Database, GeoJSON, Raster Dataset, Scanned Map, etc. Used in Facet search")

    license_info=RichTextField(null=True, blank=True)

    thumbnail = models.CharField(help_text="The URL to a static image of the resource", max_length=512, null=True, blank=True)

    harvest = models.ForeignKey(Harvest, on_delete=models.SET_NULL,null=True, blank=True)
    end_point = models.ForeignKey(End_Point, on_delete=models.SET_NULL,null=True, blank=True)

    raw_json = models.JSONField(null=True, blank=True)
    layer_json = models.JSONField(null=True, blank=True)
    # Note -  when deleting parent - system hangs - need to delete each child first - a work around has been implemented
    # see admin delete override.
    parent = models.ManyToManyField('self', blank=True, related_name='parent_resource', symmetrical=False)

    access_information = models.TextField(null=True, blank=True)

    missing = models.BooleanField(help_text="Should the endpoint no longer list this resource", null=True, blank=True)

    Status_Type = (
        ('as', 'Approved for Staging'),
        ('is', 'In Staging'),
        ('ap', 'Approved for Production'),
        ('ip', 'In Production'),
        ('nr', 'Needs Review'),
        ('rs', 'Remove from Staging'),
        ('rp', 'Remove from Production')
    )
    status_type = models.CharField(max_length=2, choices=Status_Type,default='nr')

    class Meta:
        unique_together = ("resource_id", "end_point")

    def __str__(self):
        return str(self.title)

    """
        A model mixin that tracks model fields' values and provide some useful api
        to know what fields have been changed.
        ref: https://stackoverflow.com/questions/1355150/when-saving-how-can-you-check-if-a-field-has-changed
        """

    def __init__(self, *args, **kwargs):
        super(Resource, self).__init__(*args, **kwargs)
        self.__initial = self._dict

    @property
    def diff(self):
        d1 = self.__initial
        d2 = self._dict
        diffs = [(k, (v, d2[k])) for k, v in d1.items() if v != d2[k]]
        return dict(diffs)

    @property
    def has_changed(self):
        return bool(self.diff)

    @property
    def changed_fields(self):
        return self.diff.keys()

    def get_field_diff(self, field_name):
        """
        Returns a diff for field if it's changed and None otherwise.
        """
        return self.diff.get(field_name, None)

    def save(self,user=False,community_input=None, *args, **kwargs):
        """
        Saves model and set initial state.
        """

        # saving logic - ie. change for change - store a record of the change update the overrides
        print("we are saving!!! by:",user)
        if self.has_changed:
            for f in self.changed_fields:
                need_to_track=True
                print("a change has been made",f,self.get_field_diff(f))
                d1=str(self.get_field_diff(f)[0])
                d2=str(self.get_field_diff(f)[1])
                print(d1,"VS",d2)
                #make sure a change has been made
                # if d1 !=None :
                limit =250
                change_type='a'
                if user and user =='c':
                    # community input
                    change_type='c'
                elif user:
                    change_type='u'

                # the boundary box changes slightly when saved - lets skip if we're in the admin
                if f == "bounding_box" and change_type=='u':
                    need_to_track=False

                #skip if going from None to ''
                if d2 == "None" and d1=='':
                    need_to_track=False

                if need_to_track:
                    Change_Log.objects.get_or_create(
                        change_type=change_type,
                        community_input=community_input,
                        resource=self,
                        field_name=f,
                        # truncate really long values
                        old=(d1[:limit-2] + '..') if len(d1) > limit else d1,
                        new = (d2[:limit - 2] + '..') if len(d2) > limit else d2
                    )
                    #if the field is status - create a status log record
                    if f =="status_type":
                        Status_Log.objects.get_or_create(
                            resource=self,
                            status_desc="From: "+d1+" to: "+d2
                        )


        super(Resource, self).save(*args, **kwargs)
        self.__initial = self._dict

    @property
    def _dict(self):
        return model_to_dict(self, fields=[field.name for field in
                                           self._meta.fields])
# keep track of a records status history
# todo implement this, and track the user that made the change
class Status_Log(models.Model):
   date = models.DateTimeField('Date changed', default=datetime.now, blank=True)
   resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
   status_desc = models.CharField(max_length=200)
   notes = models.TextField(null=True, blank=True)


class Georeference_Request(models.Model):
   date = models.DateTimeField('Date requested', default=datetime.now, blank=True)
   resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
   name = models.CharField(max_length=400,null=True, blank=True)
   email = models.CharField(max_length=200,null=True, blank=True)
   notes = models.TextField(null=True, blank=True)

class Community_Input(models.Model):
   date = models.DateTimeField('Date received', default=datetime.now, blank=True)
   resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
   name = models.CharField(max_length=200,null=True, blank=True)
   email = models.CharField(max_length=200,null=True, blank=True)
   field_name = models.CharField(max_length=100)
   notes = models.TextField(null=True, blank=True)

   def __str__(self):
       _str = ""
       if self.name:
           _str += self.name+" "
       if self.email:
           _str += self.email

       if _str =="":
           _str = "Community_Input "+str(self.id)
       return _str


class URL_Type(models.Model):
    name = models.CharField(max_length=100,unique=True)
    ref = models.CharField(max_length=150,help_text="The standard for the URL",null=True, blank=True)
    service = models.BooleanField(help_text="If the url has mappability.",null=True, blank=True)
    _class = models.CharField(max_length=100,null=True, blank=True,help_text="When mapping, this field directs the web map to use a specific class.")
    _method = models.CharField(max_length=100,null=True, blank=True,help_text="The method for the class is defined here.")
    def __str__(self):
        return str(self.name)

    class Meta:
        verbose_name_plural = "URL Types"

class URL_Label(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return str(self.name)

class URL(models.Model):
    url = models.CharField(max_length=512)
    url_label = models.ForeignKey(URL_Label, null=True, blank=True,on_delete=models.CASCADE)
    url_type = models.ForeignKey(URL_Type, on_delete=models.CASCADE)
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)

    class Meta:
        unique_together = (("url", "url_type", "resource"),)

    def __str__(self):
        return str(self.url)


class Change_Log(models.Model):
    field_name = models.CharField(max_length=100)
    date = models.DateTimeField('Date changed', default=datetime.now, blank=True)
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    community_input = models.ForeignKey(Community_Input, on_delete=models.CASCADE, blank=True, null=True)
    old = models.CharField(max_length=250, blank=True, null=True)
    new = models.CharField(max_length=250, blank=True, null=True)
    Change_Type = (
        ('o', 'origin'),
        ('a', 'automation'),
        ('u', 'user'),
        ('c', 'community')
    )
    change_type = models.CharField(max_length=1, choices=Change_Type)