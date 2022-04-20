from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin


from django.views.decorators.cache import never_cache
from django.contrib.admin import SimpleListFilter
from .models import Resource,End_Point,Publisher,Tag,URL,Status_Log,Owner,Type,Geometry_Type,Format,Place,Named_Place, Category,Category_Keywords,Change_Log,Community_Input, Georeference_Request,URL_Type,URL

from django.utils.safestring import mark_safe

import json
from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import HtmlFormatter
from django.db import connection

from django.contrib import messages
from django.utils.translation import ngettext

from django.http import HttpResponseRedirect
import resources.ingester.Delete_From_Solr as Delete_From_Solr
import resources.ingester.DB_ToGBL as db_to_gbl
import resources.ingester.Publish_ToGBL as publish_to_gbl
from django.shortcuts import render

import decimal
from django.contrib.gis.geos import Point, WKTWriter
from django.contrib.gis.geos import GEOSGeometry

import os
import glob
import sys
sys.setrecursionlimit(10000)

# # Register the models
# class MyModelAdmin(admin.ModelAdmin):
#     list_display = ('id', 'description')

class MyAdminSite(admin.AdminSite):
    # @never_cache
    site_header = 'Geoportal Administration'

admin_site = MyAdminSite(name='myadmin')


# allow folder editing within the node interface
class URLInline(admin.StackedInline):
    model = URL
    list_display = ('url', 'url_type', 'url_label', 'get_link', )


    fieldsets = [
        (None, {'fields': [('url','get_link')]}),
        (None, {'fields': [('url_type','url_label')]}),
        (None, {'fields': [('geo_reference')]}),
        ]
    readonly_fields = ["get_link","geo_reference"]

    extra = 0

    def get_link(self, obj):
        if obj.pk:
            html = "<a href='"+obj.url+"' target='_blank' >Go</a>"
            return mark_safe(html)
        else:
            return '-'

    get_link.short_description = ("Link")
    get_link.allow_tags = True

    def geo_reference(self, obj):
        if obj.pk and str(obj.url_type)=='image':
            corners=""
            if obj.resource.bounding_box:
                points = []
                for b in obj.resource.bounding_box:
                    for p in b:
                        points.append(str(p[0]) + " " + str(p[1]))
                corners = "&d="+','.join(points)
            solr_id=str(obj.resource.resource_id)+"-"+str(obj.resource.end_point.id)
            html = "<a href='/geo_reference?lng=-98.74&lat=36.25&z=8&id="+solr_id+"&img="+obj.url+corners+"&user="+str(1)+"' target='_blank' >Open Georeferencer</a>"
            return mark_safe(html)
        else:
            return '-'

    geo_reference.short_description = ("Geo Reference")
    geo_reference.allow_tags = True


class Status_LogInline(admin.StackedInline):
    model = Status_Log
    extra = 0

class Change_LogInline(admin.StackedInline):
    model = Change_Log
    classes = ['collapse']
    # readonly_fields = ('field_name', "date_", "change_type")
    fieldsets = [
        (None, {'fields': [('field_name', "date", "change_type")]}),
        (None, {'fields': ['new']}),
        (None, {'fields': ['old']}),
        (None, {'fields': ['community_input']})

    ]
    extra = 0

class ParentInline(admin.StackedInline):
    model = Resource.parent.through
    fk_name = "from_resource" # not work "parent_resource" "resource_id", "parent_id", from_resource_id, to_resource_id
    classes = ['collapse']
    verbose_name = "Parent Resource"
    verbose_name_plural = "Parent Resources"
    extra = 0
    show_change_link=True

class ChildrenInline(admin.StackedInline):
    model = Resource.parent.through
    fk_name = "to_resource" # not work "parent_resource" "resource_id", "parent_id", from_resource_id, to_resource_id
    classes = ['collapse']
    verbose_name = "Child Resource"
    verbose_name_plural = "Child Resources"
    extra = 0
    show_change_link=True

class ParentFilter(admin.SimpleListFilter):
    title = 'Root Resource'
    parameter_name = 'is_parent'

    def lookups(self, request, model_admin):
        return (
            ('Yes', 'Yes'),
            ('No', 'No'),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == 'Yes':
            return queryset.filter(parent=None)
        elif value == 'No':
            return queryset.exclude(parent=None)
        return queryset

# @admin.register(Resource)
class ResourceAdmin(OSMGeoAdmin):
    list_filter = ('end_point',"type","status_type","owner",ParentFilter,"missing")
    search_fields = ('title','alt_title','description','resource_id')
    list_display = ('title', 'year','end_point','get_thumb_small','type','get_category','status_type',"child_count","accessioned")

    readonly_fields = ('get_thumb',"_layer_json","_raw_json","get_tags","get_named_places","get_category","child_count","preview")
    fieldsets = [
        (None, {'fields': [('resource_id','preview'),'year','temporal_coverage']}),
        (None, {'fields': [('title', 'alt_title')]}),
        (None, {'fields': ['status_type','end_point',"missing"]}),
        (None, {'fields': [('resource_type')]}),
        (None, {'fields': [('type', 'geometry_type', "format")]}),

        (None, {'fields': ["get_thumb", "thumbnail"]}),
        (None, {'fields': [("owner", "publisher")]}),
        (None, {'fields': [("created","modified","accessioned")]}),

        (None, {'fields': ['description']}),
        (None, {'fields': ['bounding_box']}),

        (None, {'fields': ["languages","category"]}),
        (None, {'fields': [( "get_tags","tag")]}),
        (None, {'fields': [("get_named_places","named_place")]}),


        (None, {'fields': ["_raw_json"]}),
        (None, {'fields': ["_layer_json"]}),
        (None, {'fields': ["license_info"]}),

    ]

    def child_count(self, obj=None):
        with connection.cursor() as cursor:
            cursor.execute("Select count(id) from resources_resource_parent where to_resource_id={};".format(obj.id))

            return (cursor.fetchone()[0])



    def get_tags(self, obj=None):
         print(obj.tag.all())
         return ", ".join([t.name for t in obj.tag.all()])

    def get_named_places(self, obj=None):
        return ", ".join([p.name for p in obj.named_place.all()])

    def get_category(self, obj):
        return ",".join([p.name for p in obj.category.all()])

    def get_thumb(self, obj=None):
        html = '<img src="{}" alt="False">'.format(obj.thumbnail) if obj.thumbnail else ""
        return mark_safe(html)

    def get_thumb_small(self, obj=None):

        html = '<img src="{}" alt="False" width="30">'.format(obj.thumbnail) if obj.thumbnail else ""
        return mark_safe(html)

    def _raw_json(self, obj=None):
        return mark_safe(get_pretty_json(obj.raw_json))  if obj.raw_json else ""

    def _layer_json(self, obj=None):
        return mark_safe(get_pretty_json(obj.layer_json)) if obj.layer_json else ""

    inlines = [
        ParentInline,
        ChildrenInline,
        URLInline,
        Status_LogInline,
        Change_LogInline
    ]

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    actions = ["add_selected_resources_to_staging","delete_selected_resources", 'remove_selected_resources_from_index_staging']

    def add_selected_resources_to_staging(self, request, queryset):
        # first export

        directory = os.path.dirname(os.path.realpath(__file__)) + "/ingester"
        verbosity=1
        # clear the directory
        if os.path.exists(directory + "/json"):
            files = glob.glob(directory + "/json/*")
            if (verbosity>1):
                print("removing existing files from past ingest for a fresh start!")

            for f in files:
                os.remove(f)

        # associate the children
        for r in queryset:
            #todo - need a better way than just relying upon the parent status
            r.layers = Resource.objects.filter(status_type=r.status_type,parent=r.id)
            print("The layers are:",r.layers)

        exporter = db_to_gbl.DB_ToGBL({
            "resources": queryset,
            "path": directory + "/",
            "verbosity": verbosity
        })
        # then ingest
        publish_to_gbl.Publish_ToGBL({
            "path": directory + "/json",
            "verbosity": verbosity
        })
        # set status to remove from staging
        updated =queryset.update(status_type='is')
        self.message_user(request, ngettext(
            '%d resource was successfully ingested to Staging.',
            '%d resources were successfully ingested to Staging.',
            updated,
        ) % updated, messages.SUCCESS)

    add_selected_resources_to_staging.short_description = "Ingest to Staging"

    def remove_selected_resources_from_index_staging(self, request, queryset):
        deleter = Delete_From_Solr.Delete_From_Solr({})
        # set status to remove from staging
        updated =queryset.update(status_type='rs')
        for obj in queryset:
            # remove from solr
            print("DELETE---", obj.resource_id)
            deleter.interface.delete_one_record("\""+obj.resource_id+"\"")

        self.message_user(request, ngettext(
            '%d resource was successfully removed from Staging.',
            '%d resources were successfully removed from Staging.',
            updated,
        ) % updated, messages.SUCCESS)

    remove_selected_resources_from_index_staging.short_description = "Remove from Staging"

    def delete_selected_resources(self, request, queryset):

        if 'apply' in request.POST:
            # The user clicked submit on the intermediate form.
            # Perform our update action:
            # # prevent postgres from hanging - https://stackoverflow.com/questions/62439261/postgres-delete-hangs-on-a-table-with-a-self-referential-foreign-key
            with connection.cursor() as cursor:
                cursor.execute("ALTER TABLE resources_resource DISABLE TRIGGER ALL;")

            for obj in queryset:
                print("WERE DELETING SOMETHING #############")
                obj.delete()

            with connection.cursor() as cursor:
                cursor.execute("ALTER TABLE resources_resource ENABLE TRIGGER ALL;")
            # Redirect to our admin view after our update has
            # completed with a nice little info message saying
            # our models have been updated:
            self.message_user(request,
                              " {} Resources Deleted!".format(queryset.count()))
            return HttpResponseRedirect(request.get_full_path())

        return render(request,
                      'admin/delete.html',
                      context={'resources':queryset})

    def save_model(self, request, obj, form, change):

        try:
            # attempt to match precision and prevent unexpected change
            # use first point as determinant
            #todo make this more robust
            first_point = str(self.model.objects.get(id=obj.id).bounding_box[0][0][0])
            precision = len(first_point[first_point.index(".") + 1:])
            wkt_w = WKTWriter()
            wkt_w.precision = precision
            obj.bounding_box = GEOSGeometry(wkt_w.write(obj.bounding_box))
        except:
            pass
        print("first point",)
        """pass request to save to distinguish between automation and admin
              """
        obj.save(request.user)

    def preview(self, obj):
        if obj.pk:

            html = "<a href='/preview?id="+obj.resource_id+"' target='_blank' >Preview</a>"
            return mark_safe(html)
        else:
            return '-'

    preview.short_description = ("Preview")
    preview.allow_tags = True



def get_pretty_json(_json):
    """Function to display pretty version of our data REF: https://www.pydanny.com/pretty-formatting-json-django-admin.html"""
    # Convert the data to sorted, indented JSON
    response = json.dumps(_json, sort_keys=True, indent=2)

    # Get the Pygments formatter
    formatter = HtmlFormatter(style='colorful')
    # Highlight the data
    response = highlight(response, JsonLexer(), formatter)

    # Get the stylesheet
    return  "<style>" + formatter.get_style_defs() + "</style><br><div style='max-height: 500px; overflow: scroll;'>" + response+"</div>"


admin_site.register(Resource, ResourceAdmin)

class End_PointAdmin(OSMGeoAdmin):
   pass

admin_site.register(End_Point, End_PointAdmin)

class PublisherAdmin(OSMGeoAdmin):
    pass
admin_site.register(Publisher, PublisherAdmin)

class Community_InputAdmin(OSMGeoAdmin):
   list_display = ["resource","date","name", "email"]
admin_site.register(Community_Input, Community_InputAdmin)

class Georeference_RequestAdmin(OSMGeoAdmin):
   pass
admin_site.register(Georeference_Request, Georeference_RequestAdmin)


class OwnerAdmin(OSMGeoAdmin):
    # enable a full_name overwrite when available
    list_display=["name","full_name"]
    search_fields = ("name","full_name")

admin_site.register(Owner, OwnerAdmin)

class TypeAdmin(OSMGeoAdmin):
   pass
admin_site.register(Type, TypeAdmin)

class Geometry_TypeAdmin(OSMGeoAdmin):
   pass
admin_site.register(Geometry_Type, Geometry_TypeAdmin)

class FormatAdmin(OSMGeoAdmin):
   pass
admin_site.register(Format, FormatAdmin)


class Category_KeywordsInline(admin.StackedInline):
    model = Category_Keywords.category.through
    extra = 0

class Category_KeywordsAdmin(OSMGeoAdmin):
    pass
admin_site.register(Category_Keywords, Category_KeywordsAdmin)

class CategoryAdmin(OSMGeoAdmin):
    inlines = [
        Category_KeywordsInline
    ]
admin_site.register(Category, CategoryAdmin)


class TagAdmin(OSMGeoAdmin):
   pass
admin_site.register(Tag, TagAdmin)

class PlaceAdmin(OSMGeoAdmin):
   pass
admin_site.register(Place, PlaceAdmin)

class Named_PlaceAdmin(OSMGeoAdmin):
   pass
admin_site.register(Named_Place, Named_PlaceAdmin)

class URL_TypeAdmin(OSMGeoAdmin):
    list_display = ('name', 'ref', 'service', '_class', '_method')

admin_site.register(URL_Type,URL_TypeAdmin)

class URLAdmin(OSMGeoAdmin):
    list_filter = ("url_type",)

admin_site.register(URL,URLAdmin)

