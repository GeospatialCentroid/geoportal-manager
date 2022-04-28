from django.shortcuts import render
import urllib.request, json
from django.http import HttpResponse, HttpResponseRedirect
from django.core.serializers.json import DjangoJSONEncoder
from django.template.response import TemplateResponse

from django.conf import settings


from resources.models import Resource,Community_Input,End_Point,URL_Type

from django.http import JsonResponse
from django.core import serializers


from . import html_generation

from . import details_view

from . import utils

from django.contrib.auth.decorators import login_required

import resources.ingester.DB_ToGBL as db_to_gbl


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
    args["browse_html"] = html_generation.get_browse_html(request)

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

                if len(result_data['response']['docs'])>0 and "dct_isPartOf_sm" in result_data['response']['docs'][0] and parts[1]=="sub_details":
                    # load the sub records
                    args["sub_result_html"] = html_generation.get_results_html("q=dct_isPartOf_sm:"+result_data['response']['docs'][0]["dct_isPartOf_sm"][0]+".layer&rows=1000", _LANG=False)

    start=10
    if request.GET.get('start'):
        start += int(request.GET.get('start'))
    f=""
    if request.GET.get('f'):
        f=request.GET.get('f')
    args["next_url"] = "/?f="+f+"&start="+str(start)


    return render(request, 'geoportal/index.html', args)

@login_required(login_url='/accounts/login/')
def preview(request,_LANG=False):
    return index(request, _LANG)

@login_required(login_url='/accounts/login/')
def generate_gbl_record(request,_LANG=False):
    # takes the id, creates the gbl record and returns the result
    r = Resource.objects.get(resource_id=request.GET.get('id'))

    # todo - need a better way than just relying upon the parent status
    r.layers = Resource.objects.filter(status_type=r.status_type, parent=r.id)

    exporter = db_to_gbl.DB_ToGBL({
        "resources": [r],
        "verbosity": 1
    })
    #return the first as there should ohly be one
    return HttpResponse(json.dumps(exporter.exported[0]), content_type='application/json')


def result_page(request,_LANG=False):
    # for loading relative items dynamically
    args = {}
    args["result_html"] = html_generation.get_results_html(request,_LANG)

    return TemplateResponse(request, 'geoportal/result.html', args)




def resource_page(request,resource_id,_LANG=False):
    result_data= utils.get_reference_data(resource_id)

    args = details_view.get_details_args(result_data,False, request.build_absolute_uri("/"))
    return TemplateResponse(request, 'resource/index.html', args)


def details_page(request,resource_id,_LANG=False):
    # for loading relative items dynamically
    print("We have preview id",request.GET.get('id'))
    if request.GET.get('id'):
        data = generate_gbl_record(request).content.decode('utf8')
        # convert the data to the expected solr structure
        result_data = {'response':{'docs':[json.loads(data)]}}

        print("result_data ((((((((((",result_data)
    else:
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



def get_disclaimer(request):
   if request.GET.get('e'):
       e = End_Point.objects.get(id=request.GET.get('e'))
       return HttpResponse(e.disclaimer)


def get_url_types(request):
   url_types = URL_Type.objects.values('name', 'ref', '_class', '_method')

   return HttpResponse(json.dumps(list(url_types)), content_type='application/json')

def get_services(request):
   url_types = URL_Type.objects.filter(service=True).values('name', 'ref', '_class','_method')

   return HttpResponse(json.dumps(list(url_types)), content_type='application/json')

def get_suggest(request):
    if request.GET.get('q'):
        _url = settings.SOLR_URL
        print(_url + "suggest?suggest.q=" + request.GET.get('q'))
        suggest = urllib.request.urlopen(_url + "suggest?suggest.q=" + request.GET.get('q'))
        data= json.load(suggest)
        suggestions=data["suggest"]["mySuggester"][urllib.parse.unquote(request.GET.get('q'))]["suggestions"]

        return HttpResponse(json.dumps(suggestions, cls=DjangoJSONEncoder), content_type='application/json')


def get_rss(request):
    # for showing latest records
    _url = settings.SOLR_URL
    args={}
    args["docs"] = get_solr_data("q=*:*%20AND%20solr_type:parent&sort=gbl_mdModified_dt%20desc")["response"]["docs"]
    args["base_url"] = settings.BASE_URL
    return TemplateResponse(request, 'geoportal/rss.html', args, content_type="application/xml")
