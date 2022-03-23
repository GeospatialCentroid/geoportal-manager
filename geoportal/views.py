from django.shortcuts import render
import urllib.request, json
from django.http import HttpResponse, HttpResponseRedirect
from django.core.serializers.json import DjangoJSONEncoder
from django.template.response import TemplateResponse

from django.conf import settings

from django.contrib.gis.geos import GEOSGeometry
from resources.models import Resource,Community_Input,End_Point,URL_Type

from django.http import JsonResponse
from django.core import serializers

from django.views.decorators.csrf import csrf_exempt

from . import html_generation

from . import details_view

from . import utils

fq="&fq=solr_type:parent"
child_filter="&childFilter={!edismax v=$q.user}"
fl="&fl=*,[child childFilter=$childFilter  limit=1000]"
# adding accommodation for child searching
# note the space in front for '&q= ' this is really important!
q= "&q= {!parent which=solr_type:parent v=$q.child} OR {!edismax v=$q.user}"
q_child="&q.child=%2Bsolr_type:child  %2B{!edismax v=$q.user}" # note '+' replaced with %2B
q_user="&q.user="
base_search=fq+child_filter+fl+q+q_child+q_user

def index(request,_LANG=False):
    # for loading relative items dynamically
    args = {'STATIC_URL': settings.STATIC_URL}
    args['GOOGLE_ANALYTICS_ID']= settings.GOOGLE_ANALYTICS_ID
    args["browse_html"] = html_generation.get_browse_html()

    # when a filter is set - load the results
    if request.GET.get('f'):
        args["result_html"] = html_generation.get_results_html(request, _LANG)
    else:
        # when no filter simply access first page of results
        # args["result_html"] = html_generation.get_results_html("json = {query: 'gbl_suppressed_b:False'}", _LANG)
        # Added parent filter
        print("pre--base_search------",base_search)
        args["result_html"] = html_generation.get_results_html(base_search.replace(" ","%20")+"*:*", _LANG)

    # http://localhost:8000/?f=!(!f,CRB_California)&e=(c:~36.527294814546245,-98.87695312500001~,z:3)&l=!()&t=search_tab/sub_details/7949bb91a02741a7961712a7b81b7b9e_7&rows=10
    if request.GET.get('t'):
        parts=request.GET.get('t').split("/")
        if len(parts)>2:

            if(parts[1]=="sub_details" or parts[1]=="details"):
                # load the child dtails to the sub_details element
                # load all the child results for the parent
                print("-----------")
                # how do we make sure to load the child information into the sub_details
                result_data = utils.get_reference_data(parts[2])

                sub_args = details_view.get_details_args(result_data, _LANG,parts[1]=="sub_details",request.build_absolute_uri("/"))
                if sub_args is not None:
                    for a in sub_args:
                        args[a] = sub_args[a]

                if len(result_data['response']['docs'])>0 and "dct_source_sm" in result_data['response']['docs'][0] and parts[1]=="sub_details":
                    # load the sub records
                    args["sub_result_html"] = html_generation.get_results_html("q=path:"+result_data['response']['docs'][0]["dct_source_sm"][0]+".layer&rows=1000", _LANG=False)

    start=10
    if request.GET.get('start'):
        start += int(request.GET.get('start'))
    f=""
    if request.GET.get('f'):
        f=request.GET.get('f')
    args["next_url"] = "/?f="+f+"&start="+str(start)


    return render(request, 'geoportal/index.html', args)

def result_page(request,_LANG=False):
    # for loading relative items dynamically
    args = {}
    args["result_html"] = html_generation.get_results_html(request,_LANG)

    return TemplateResponse(request, 'geoportal/result.html', args)

def geo_reference(request):
    # for loading relative items dynamically
    args = {'STATIC_URL': settings.STATIC_URL}
    return render(request, 'geo_reference/index.html', args)


def resource_page(request,resource_id,_LANG=False):
    result_data= utils.get_reference_data(resource_id)

    args = details_view.get_details_args(result_data,False, request.build_absolute_uri("/"))
    return TemplateResponse(request, 'resource/index.html', args)


def details_page(request,resource_id,_LANG=False):
    # for loading relative items dynamically
    result_data = utils.get_reference_data(resource_id)

    args = details_view.get_details_args(result_data,_LANG,False,request.build_absolute_uri("/"))
    return TemplateResponse(request, 'resource/details.html', args)


def resource_admin_delete_page(request):
    args = {}
    if request.GET.get('ids'):
        args['ids'] = request.GET.get('ids')

    return TemplateResponse(request, 'admin/delete.html', args)

def resource_admin_page(request,resource_id):
    # for loading relative items dynamically
    args = {'STATIC_URL': settings.STATIC_URL}

    args["data"]= get_solr_data("q=dct_identifier_sm:" + str(resource_id))

    return JsonResponse( args["data"])



def fetch_solr(request):
    print("------fetch_solr--------")
    data = get_solr_data(request.META['QUERY_STRING'])
    return HttpResponse(json.dumps(data, cls=DjangoJSONEncoder), content_type='application/json')

def get_solr_data(_query):
    _url = settings.SOLR_URL
    print(_url + "select?" +_query)
    request = urllib.request.urlopen(_url + "select?" +_query)
    return json.load(request)

@csrf_exempt
def set_geo_reference(request):

    # note the id is actually two parts the resource_id and the endpoint id
    solr_id_parts = request.GET.get('id').rsplit('-', 1)
    resource_id =solr_id_parts[0]
    end_point_id =solr_id_parts[1]
    print(resource_id,end_point_id)
    # when an image is georeferenced the values are saved with the resource for distortion in public facing interface
    r = Resource.objects.get(resource_id=resource_id, end_point_id=end_point_id)

    c = False
    # get the patron name and email
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        c = Community_Input.objects.create(name=name, email=email,field_name="bounding_box",resource=r)

    r.bounding_box=GEOSGeometry("POLYGON((" + request.GET.get('d') + "))", srid=4326)

    # pass c - for community to identify the source of the change
    r.save('c',c)
    return HttpResponse(json.dumps({'complete': True}, cls=DjangoJSONEncoder), content_type='application/json')

def get_disclaimer(request):
   if request.GET.get('e'):
       e = End_Point.objects.get(id=request.GET.get('e'))
       return HttpResponse(e.disclaimer)

def get_services(request):
   url_types = URL_Type.objects.filter(service=True).values('name', 'ref', '_class','_method')

   return HttpResponse(json.dumps(list(url_types)), content_type='application/json')

def get_suggest(request):
    if request.GET.get('q'):
        _url = settings.SOLR_URL
        print(_url + "suggest?suggest.q=" + request.GET.get('q'))
        suggest = urllib.request.urlopen(_url + "suggest?suggest.q=" + request.GET.get('q'))
        data= json.load(suggest)
        suggestions=data["suggest"]["mySuggester"][request.GET.get('q')]["suggestions"]
        return HttpResponse(json.dumps(suggestions, cls=DjangoJSONEncoder), content_type='application/json')