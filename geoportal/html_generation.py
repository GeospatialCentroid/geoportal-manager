from . import views

import  json

from datetime import datetime



from . import rison

from . import utils

from urllib.parse import unquote,urlparse,quote_plus



def get_browse_html(_LANG=False):
    # for SEO - render html serverside
    # facets = views.get_solr_data("q=*:*%20AND%20gbl_suppressed_b:False&rows=0&facet.mincount=1&facet=on&wt=json")
    # added parent filter
    facets = views.get_solr_data("q=*:*&rows=0&facet.mincount=1&facet=on&wt=json&fq={!parent%20which='solr_type:parent'}")
    args={}
    args['LANG'] = utils.get_lang(_LANG)

    html = '<ul class="list-group list-group-flush">'

    html += get_list_group_html(-1,args['LANG']["FACET"]["TOPICS"], facets["facet_counts"]["facet_fields"]["dct_subject_sm"],
                                     "dct_subject_sm", args['LANG']["FACET"]["CATEGORIES"], True, "true")

    # html += get_list_group_html(-2, args['LANG']["FACET"]["PRODUCERS"],
    #                             facets["facet_counts"]["facet_fields"]["dct_publisher_s"],
    #                             "dct_publisher_sm", False, True, "true")
    # html += get_list_group_html(-2, args['LANG']["FACET"]["KEYWORDS"],
    #                             facets["facet_counts"]["facet_fields"]["b1g_keyword_sm"],
    #                             "b1g_keyword_sm", False, False, "true")

    html += get_list_group_html(-3,args['LANG']["FACET"]["PLACE"], facets["facet_counts"]["facet_fields"]["dct_spatial_sm"],
                                     'dct_spatial_sm', False, False, "true")
    html += get_list_group_html(-4,args['LANG']["FACET"]["AUTHOR"], facets["facet_counts"]["facet_fields"]["dct_creator_sm"],
                                     "dct_creator_sm", False, False, "true")
    # html += get_list_group_html(-5, args['LANG']["FACET"]["DATA_TYPE"],
    #                             facets["facet_counts"]["facet_fields"]["gbl_resourceType_sm"],
    #                             "gbl_resourceType_sm", False, False, "true")
    html += get_list_group_html(-6, args['LANG']["FACET"]["FORMAT"],
                                facets["facet_counts"]["facet_fields"]["dct_format_s"],
                                "dct_format_s", False, False, "true")

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
    # Add paging and sorting url params
    rows = "1000"
    start = ""
    sort = ""

    fq = ""
    is_request=hasattr(request, "GET")

    if is_request and request.GET.get('f') is not None:
        filter_param = request.GET.get('f')

        f = ("!("+unquote(filter_param)+")").replace("~","'")
        # get the filter string for all the parents
        filter_str,has_parent_path = get_filter_str(rison.loads(f))
        # if no path is specified - restrict results to parents
        if not has_parent_path:
            filter_str= views.base_search+filter_str
            fq=views.fq
        else:
            filter_str= "&q="+filter_str+"&df=text"



        if request.GET.get('rows') is not None:
            rows= "&rows=" + str(request.GET.get('rows'))
        if request.GET.get('start') is not None:
            start="&start=" + request.GET.get('start')


        if request.GET.get('sort') is not None:
            sort = "&sort=" + request.GET.get('sort')
        else:
            # relevance
            sort = "&sort=score asc"

    elif is_request and hasattr(request, "META"):
        # get the parent
        filter_str=request.META['QUERY_STRING']
    else:
        filter_str = request

    # perform a search
    print("we're performing a search -------------- ",filter_str+rows+start+sort+fq)
    data = views.get_solr_data((filter_str+rows+start+sort+fq).replace(" ","%20"))
    LANG = utils.get_lang(_LANG)

    end_points=utils.get_endpoints()

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

        html += "<li class='list-group-item' "
        if "locn_geometry" in resource:
            html+=" onmouseenter='filter_manager.show_bounds_str(\"" + resource["locn_geometry"] + "\")'"
        html +=  " onmouseleave='filter_manager.hide_bounds()' >"

        if 'thumbnail_path_ss' in resource:
            html += "<div class='item_thumb_small'><img src="+resource["thumbnail_path_ss"]+"></div>"

        html += get_resource_header_html(resource,LANG,str(index_number)+". ")
        html += get_resource_button_html(resource,LANG)
        html += " "+get_resource_icon(resource)
        html += " " + utils.get_publisher_icon(resource,end_points)
        html += " " + utils.get_access_icon(resource)
        html+="</li>"

    html+="</ul>"

    return html
def get_filter_str(filter_arr):
    """

    :param filter_arr:
    :return: modified filter array, and flag for parent path
    """
    has_parent_path=False
    filter_str_array=[]
    # compile a url to fetch the filtered results
    for i in range(len(filter_arr)):
        f = filter_arr[i]
        f_id = str(f[0]) + ":"
        if f[0] == False:
            f_id=''
            if f[1] !='':
                filter_str_array.append(f_id + "" + f[1] + "")
        elif f[0] == "locn_geometry" or f[0] == "dct_issued_s":
            filter_str_array.append(f_id + "" + f[1] + "")
        else:
            # be sure to encapsulate facet spaces
            filter_str_array.append(f_id + "\"" + f[1] + "\"")

        # set e parent path
        if f[0] == "path":
            has_parent_path=True

    # restrict suppressed
    filter_str_array.append("gbl_suppressed_b:False")

    return " AND ".join(filter_str_array),has_parent_path

def get_resource_header_html(resource,LANG,num):
    html = ""
    title =resource["dct_title_s"]

    producer =""
    if "dct_creator_sm" in resource:
        producer = ".".join(resource["dct_creator_sm"])

    published=""
    if "dct_issued_s" in resource:
        published = datetime.strptime(resource["dct_issued_s"], "%Y-%m-%dT%H:%M:%SZ").strftime("%d-%m-%Y")

    format = ""
    if "dct_format_s" in resource:
        format = resource["dct_format_s"]

    html +="<div class='item_title font-weight-bold'>"+num+title+"</span></div>"

    html +="<div class='item_label'>"+LANG["RESULT"]["AUTHOR"]+": <span class='font-weight-bold'>"+producer+"</span></div>"
    html +="<div class='item_label'>"+LANG['RESULT']["DATE_PUBLISHED"]+": <span class='font-weight-bold'>"+published+"</span></div>"
    if format != "":
        html +="<div class='item_label'>"+LANG["RESULT"]["DATA_FORMAT"]+": <span class='font-weight-bold'>"+format+"</span></div>"
    return html

def get_resource_button_html(resource,LANG,no_details=False):
    # generate the html for navigating the resources
    html=""
    download_link = utils.get_ref_link(resource,"download")

    html += utils.get_toggle_but_html(resource,LANG)

    if "locn_geometry" in resource:
        html +="<button type='button' class='btn btn-primary' onclick='filter_manager.zoom_layer(\""+resource["locn_geometry"]+"\")'>"+LANG["RESULT"]["ZOOM"]+"</button>"

    if download_link:
      html +="<button type='button' class='btn btn-primary' onclick='window.open(\""+download_link+"\")'>"+LANG["DOWNLOAD"]["DOWNLOAD_BUT"]+"</button>"

    if not no_details:
        html += utils.get_details_but_html(resource,LANG)

    return html


def get_resource_icon(resource):
    # get all the icons
    #todo use the 'dct_accessRights_s' icon for public data to show an open padlock
    html=""
    if "gbl_resourceType_sm" in resource:
        html+=utils.get_geom_type_icon(resource["gbl_resourceType_sm"])
    return html




