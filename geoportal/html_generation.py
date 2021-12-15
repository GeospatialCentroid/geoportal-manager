from . import views

import  json

from datetime import datetime



from . import rison

from . import utils

from urllib.parse import unquote,urlparse,quote_plus

from resources.models import Resource,End_Point


def get_browse_html(_LANG=False):
    # for SEO - render html serverside
    # facets = views.get_solr_data("q=*:*%20AND%20suppressed_b:False&rows=0&facet.mincount=1&facet=on&wt=json")
    # added parent filter
    facets = views.get_solr_data("q=*:*&rows=0&facet.mincount=1&facet=on&wt=json&fq={!parent%20which='solr_type:parent'}")
    args={}
    args['LANG'] = utils.get_lang(_LANG)

    html = '<ul class="list-group list-group-flush">'

    html += get_list_group_html(-1,args['LANG']["FACET"]["TOPICS"], facets["facet_counts"]["facet_fields"]["dc_subject_sm"],
                                     "dc_subject_sm", args['LANG']["FACET"]["CATEGORIES"], True, "true")
    # html += get_list_group_html(-2, args['LANG']["FACET"]["KEYWORDS"],
    #                             facets["facet_counts"]["facet_fields"]["b1g_keyword_sm"],
    #                             "b1g_keyword_sm", False, False, "true")

    html += get_list_group_html(-3,args['LANG']["FACET"]["PLACE"], facets["facet_counts"]["facet_fields"]["dct_spatial_sm"],
                                     'dct_spatial_sm', False, False, "true")
    html += get_list_group_html(-4,args['LANG']["FACET"]["AUTHOR"], facets["facet_counts"]["facet_fields"]["dc_creator_sm"],
                                     "dc_creator_sm", False, False, "true")
    html += get_list_group_html(-5, args['LANG']["FACET"]["DATA_TYPE"],
                                facets["facet_counts"]["facet_fields"]["layer_geom_type_s"],
                                "layer_geom_type_s", False, False, "true")
    html += get_list_group_html(-6, args['LANG']["FACET"]["FORMAT"],
                                facets["facet_counts"]["facet_fields"]["dc_format_s"],
                                "dc_format_s", False, False, "true")

    #

    # todo show latest feed
    # html += LANG.FACET.NEW_DATA

    html += '</ul>'
    return html



##
def get_list_group_html(id,title, list,facet_name,translate,no_collapsed,reset):
    # for ease of access - generate facet links which filter the content

    collapse='collapse'
    collapse_but='<span class="mr-3"></span>'
    if (no_collapsed):
      collapse=''
      collapse_but=''

    html = '<li  class="list-group-item px-0"><a  role="button" class="btn collapsed" data-toggle="'+collapse+'" href="#collapse'+str(id)+'"  aria-expanded="true" aria-controls="collapse'+str(id)+'">'
    html+=title
    html+=collapse_but

    html+='</a>'

    html+='<div class="'+collapse+'" id="collapse'+str(id)+'">'
    html+='<div class="card card-body mt-2">'
    html+="<ul class='list-group'>"

    for i in range(len(list)):
        if i % 2 == 0:
            params='!('+facet_name+','+list[i]+')'
            html +='<a '
            html += ' onclick="filter_manager.add_filter(\'' + facet_name + '\',\'' + list[i] + '\',' + reset + ')"'
            html += ' href="/?f='+params+ '"'
            html += ' class="list-group-item d-flex justify-content-between align-items-center lil_pad"'
            html +=">"
            title =list[i]
            if translate:
               if list[i] in translate:
                    title =translate[list[i]]['title']

            html +=title
            html +='<span class="badge badge-primary badge-pill">'+str(list[i+1])+'</span>'
            html +='</a>'

    html+='</ul></div></div></li>'

    return html

##
def get_results_html(request,_LANG=False):
    #",sort:'geom_area asc'"
    # generate the results html
    # this html can be appended to when scrolling is performed

    html=""
    rows = ""
    start = ""
    sort = ""
    fq = ""
    is_request=hasattr(request, "GET")

    if is_request and request.GET.get('f') is not None:
        filter_param = request.GET.get('f')

        f = ("!("+unquote(filter_param)+")").replace("~","'")

        filter_str = get_filter_str(rison.loads(f))

        # Add paging and sorting url params
        rows = ""
        start= ""

        if request.GET.get('rows') is not None:
            rows= "&rows=" + str(request.GET.get('rows'))
        if request.GET.get('start') is not None:
            start="&start=" + request.GET.get('start')


        if request.GET.get('sort') is not None:
            sort = "&sort=" + request.GET.get('sort')
        else:
            # relevance
            sort = "&sort=score asc"

        # if request.GET.get('fq') is not None:
        #     rows = "&fq=" + str(request.GET.get('fq'))
        fq=views.fq

    elif is_request and hasattr(request, "META"):
        # get the parent
        filter_str=request.META['QUERY_STRING']
    else:
        filter_str = request

    # perform a search
    data = views.get_solr_data((filter_str+rows+start+sort+fq).replace(" ","%20"))
    LANG = utils.get_lang(_LANG)

    end_points=get_endpoints()

    #start with paging details
    page_count = data["response"]["numFound"]
    totals_results=page_count
    showing_start=1
    showing_end=len(data["response"]["docs"])

    # create the initial list of results
    html += '<ul class="list-group" data-total_results="'+str(totals_results)+'" data-showing_start="'+str(showing_start)+'" data-showing_end="'+str(showing_end)+'">'
    for i in range(len(data["response"]["docs"])):
        index_number=i+int(data["response"]["start"])+1
        resource=data["response"]["docs"][i]
        solr_geom=""
        if "solr_geom" in resource:
            solr_geom = resource["solr_geom"]
        html+="<li class='list-group-item' onmouseenter='filter_manager.show_bounds_str(\""+solr_geom+"\")' onmouseleave='filter_manager.hide_bounds()' >"
        html += get_resource_header_html(resource,LANG,str(index_number)+". ")
        html+= get_resource_button_html(resource,LANG)
        html+= " "+get_resource_icon(resource)
        html += " " + get_publisher_icon(resource,end_points)
        html += " " + utils.get_access_icon(resource)
        html+="</li>"

    html+="</ul>"

    return html
def get_filter_str(filter_arr):
    filter_str_array=[]
    # compile a url to fetch the filtered results
    for i in range(len(filter_arr)):
        f = filter_arr[i]
        f_id = str(f[0]) + ":"
        if f[0] == False:
            f_id=''
            filter_str_array.append(f_id + "" + f[1] + "")
        if f[0] == "solr_geom" or f[0] == "dct_issued_s":
            filter_str_array.append(f_id + "" + f[1] + "")
        else:
            # be sure to encapsulate facet spaces
            filter_str_array.append(f_id + "\"" + f[1] + "\"")

    # restrict suppressed
    filter_str_array.append("suppressed_b:False")
    #return "json={query:'" + " AND ".join(filter_str_array) + "'}"
    return  views.base_search+" AND ".join(filter_str_array)

def get_resource_header_html(resource,LANG,num):
    html = ""
    title =resource["dc_title_s"]

    producer =""
    if "dc_creator_sm" in resource:
        producer = ".".join(resource["dc_creator_sm"])

    published=""
    if "dct_issued_s" in resource:
        published = datetime.strptime(resource["dct_issued_s"], "%Y-%m-%dT%H:%M:%SZ").strftime("%d-%m-%Y")

    format = ""
    if "dc_format_s" in resource:
        format = resource["dc_format_s"]

    html +="<div class='item_title font-weight-bold'>"+num+title+"</span></div>"

    html +="<div class='item_label'>"+LANG["RESULT"]["AUTHOR"]+": <span class='font-weight-bold'>"+producer+"</span></div>"
    html +="<div class='item_label'>"+LANG['RESULT']["DATE_PUBLISHED"]+": <span class='font-weight-bold'>"+published+"</span></div>"
    html +="<div class='item_label'>"+LANG["RESULT"]["DATA_FORMAT"]+": <span class='font-weight-bold'>"+format+"</span></div>"
    return html

def get_resource_button_html(resource,LANG,no_details=False):
    # generate the html for navigating the resources
    html=""
    download_link = utils.get_ref_link(resource,"download")
    solr_geom = ""
    if "solr_geom" in resource:
        solr_geom= resource["solr_geom"]

    html += utils.get_toggle_but_html(resource,LANG)

    if solr_geom:
        html +="<button type='button' class='btn btn-primary' onclick='filter_manager.zoom_layer(\""+solr_geom+"\")'>"+LANG["RESULT"]["ZOOM"]+"</button>"

    if download_link:
      html +="<button type='button' class='btn btn-primary' onclick='window.open(\""+download_link+"\")'>"+LANG["DOWNLOAD"]["DOWNLOAD_BUT"]+"</button>"

    if not no_details:
        html += utils.get_details_but_html(resource,LANG)

    return html


def get_resource_icon(resource):
    # get all the icons
    #todo use the 'dc_rights_s' icon for public data to show an open padlock
    html=""
    if "layer_geom_type_s" in resource:
        html+=utils.get_geom_type_icon(resource["layer_geom_type_s"])
    return html


def get_publisher_icon(resource,end_points):
    html = ""
    for e in end_points:
        for p in resource["dc_publisher_sm"]:
            if p == e[0] and e[1]:
                html += '<div class="pub_icon"><img src="'+e[1]+'"></div>'

    return html

def get_endpoints():
   return End_Point.objects.values_list('name', 'thumbnail')