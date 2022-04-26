import json
from . import views

import re

from resources.models import Resource,End_Point,URL_Type

def get_lang(_LANG):
    if not _LANG:
        _LANG = 'en'
    return json.load(open('static/i18n/' + _LANG + '.json'))  # deserializes it

def clean_json(_json_refs):
    if type(_json_refs) is dict:
        json_refs = _json_refs
    else:
        try:
            json_refs = json.loads(_json_refs)

        except:
            json_refs =None
    return json_refs

def get_ref_link(_json_refs,_type):
    # look for link with type ...
    json_refs = clean_json(_json_refs)

    if json_refs:

        for j in json_refs:
            ref = get_ref_type(j)
            if ref == _type:
                    # not list and type(json_refs[j]) is not dict
                    # print("get_ref_link found",_type,type(json_refs[j]),json_refs[j])
                    if type(json_refs[j]) is not list and json_refs[j].find("[")>-1:
                        return json_refs[j].replace('[', '').replace(']', '').split(",")
                    elif type(json_refs[j]) is list:
                        # we have a list - consider adjustment for conformance
                        return json_refs[j]
                    else:
                        return json_refs[j]
    else:
        return None


def get_service_link(_json_refs):

    json_refs = clean_json(_json_refs)
    if json_refs:
        url_types = URL_Type.objects.filter(service=True).values('name', 'ref', '_class', '_method')
        print(url_types)
        for j in json_refs:
            for u in url_types:
                print("compare:",u["ref"],"to",j)
                if u["ref"]==j:
                    return True

    return False


def get_ref_type(_ref):
    '''

    :param _ref:
    :return: gets the name from the URL_type
    '''

    services = views.get_url_types(None)
    for s in  json.loads(services.content):
        if _ref == s["ref"]:
            return s["name"]
    return ""
    # if _ref == 'http://schema.org/url':
    #     return "info_page"
    # elif _ref == 'http://www.isotc211.org/schemas/2005/gmd/':
    #     return "metadata"
    # elif _ref == 'http://schema.org/downloadUrl':
    #     return "download"
    # elif _ref == 'https://schema.org/ImageObject':
    #     return "image"
    # elif _ref == 'http://iiif.io/api/image':
    #     return "iiif"
    # else:
    #     return ""

def get_toggle_but_html(resource,LANG):

    add_func = "layer_manager.toggle_layer"

    add_txt = LANG["RESULT"]["ADD"]
    #

    child_arr=[]
    # take the embedded _childDocuments_ and show those children

    if "_childDocuments_" in resource and len(resource["_childDocuments_"]) > 0:
        # get dynamic add text - get all the ids for use in determining if on map
        child_arr = get_child_array(resource["_childDocuments_"])

        add_txt = get_count_text(resource,LANG)
        add_func = "filter_manager.get_layers"
    elif "lyr_count" in resource and resource["lyr_count"]>1:
        # get dynamic add text - get all the ids for use in determining if on map
        child_arr = get_child_array(views.get_solr_data("q=dct_isPartOf_sm:"+resource["id"]+".layer&fl=id&rows=1000")["response"]["docs"])

        add_txt = get_count_text(resource,LANG)
        add_func = "filter_manager.get_layers"


    #Allow button to remain active
    # extra_class= "active"
    if (add_txt!=LANG["RESULT"]["REMOVE"]):
        extra_class=""

    print(add_txt == LANG["RESULT"]["ADD"],"get_service_link",get_service_link(resource["dct_references_s"]) )

    if(add_txt == LANG["RESULT"]["ADD"]):
        # check for add link
        if "dct_references_s" in resource and not get_service_link(resource["dct_references_s"]):
            return ""

    #todo support multiple
    if type(resource[ "dct_identifier_sm"])==list:
        resource["dct_identifier_sm"]=resource[ "dct_identifier_sm"][0]
    return "<button type='button' id='" + resource["dct_identifier_sm"] + "_toggle' class='btn btn-primary " + resource[ "dct_identifier_sm"] + "_toggle " + extra_class + "' data-child_arr=\"" + ",".join( child_arr) + "\" onclick=\"" + add_func + "(\'" + resource["dct_identifier_sm"] + "\',this)\">" + add_txt + "</button>"

def get_child_array(children):
    """

    :param children:
    :return:
    """
    child_arr = []
    for c in children:
        child_arr.append(c["id"])
    return child_arr

def get_count_text(resource,LANG):
    #
    if "_childDocuments_" in resource and len(resource["_childDocuments_"]) > 0:
        return LANG["RESULT"]["ADD"] + " - <span></span>" + "<span>/" + str(len(resource["_childDocuments_"])) + "</span>"
    else:
        return LANG["RESULT"]["ADD"] + " - <span></span>" + "<span>/" + str(resource["lyr_count"]) + "</span>"


def get_details_but_html(resource,LANG):
    return "<button type='button' class='btn btn-primary' href='"+get_catelog_url(resource)+"' onclick=\"filter_manager.show_details(\'" + resource["dct_identifier_sm"] + "\')\">" + \
           LANG["RESULT"]["DETAILS"] + "</button>"

def get_catelog_link_html(resource,LANG):
    return '<a href ="'+get_catelog_url(resource)+'" target="_blank">'+LANG["DETAILS"]["CATALOG_VIEW"]+'</a>'

def get_catelog_url(resource):
    panel = "details"
    # for child layers

    if "dct_isPartOf_sm" in resource:
        panel = "sub_details"

    if type(resource["dct_identifier_sm"]) == list:
        resource["dct_identifier_sm"]=resource["dct_identifier_sm"][0]
    return "?t=search_tab/"+panel+"/"+resource["dct_identifier_sm"]

def get_geom_type_icon(_geom_type):
    # returns an html icon
    if _geom_type == 'Image':
        return '<i class="far fa-image"></i>'
    elif _geom_type == 'Raster':
        return '<i class="fas fa-globe-americas"></i>'
    elif _geom_type == 'Point':
        return '<i class="fas fa-map-marker-alt"></i>'
    elif _geom_type == 'Polygon':
        return '<i class="fas fa-vector-square"></i>'
    elif _geom_type == 'Line':
        return '<div style="width:12px;height:12px;display:inline-block;"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" aria-labelledby="aria-label-line">'+\
            '<rect x="2" y="22.9" width="7.1" height="7.1" style="stroke-width:3;stroke:#333;fill-opacity:0;" />'+\
            '<rect x="22.9" y="2" width="7.1" height="7.1" style="stroke-width:3;stroke:#333;fill-opacity:0;" />'+\
            '<path fill="none" stroke="#333" stroke-miterlimit="10" stroke-width="3" d="M9.1 22.9L22.9 9.1"></path></svg></div>'
    else:
        return ""

def get_access_icon(resource):
    html = "<i class='fas fa-lock'></i>"
    if resource['dct_accessRights_s'] == "Public":
        html = "<i class='fas fa-unlock'></i>"
    return html

def get_reference_data(resource_id):
    return views.get_solr_data("q=dct_identifier_sm:" + str(resource_id).replace(":","\:"))

def get_more_details_link_html(resource,LANG):
    info_link= None
    if 'dct_references_s' in resource:
        info_link=get_ref_link(resource['dct_references_s'], "info_page")
    if info_link:
        html=""
        if isinstance(info_link, str):
            html += get_more_details_link(info_link, LANG)
        else:
            for i in info_link:
                html+= get_more_details_link(i,LANG)

        return html
    else:
        return ""

def get_more_details_link(url,LANG):
    return '<a href="' + url + '" target="_blank">' + LANG["DETAILS"][
        "MORE_DETAILS"] + ' <i class="fas fa-external-link-alt"></i></a><br/>'

def get_fields_html(_fields,lang):
    """
    Convert the solr field into a pretty table
    :param _fields:
    :return: html
    """
    html='<span class="font-weight-bold">'+lang["DETAILS"]["ATTRIBUTES"]+':</span><br/>'
    html+="<table class='attr_table'>"
    html += "<tr><th>"+lang["DETAILS"]["NAME"]+"</th><th>"+lang["DETAILS"]["TYPE"]+"</th></tr>"
    for f in _fields:
        try:
            i = convert_text_to_json(f)
            if type(i) is dict:
                html += get_fields_row_html(i,lang)
            else:
                for j in i:
                    if type(j) is dict:
                        html += get_fields_row_html(j, lang)
                    else:
                        html +=""
        except:
            return ""

    return html+"</table><br/>"

def get_fields_row_html(j,lang):
    html=""
    int_type = ["esriFieldTypeOID", "esriFieldTypeSingle", "esriFieldTypeDouble"]
    if 'type' in j:
        type_str = j['type']
        if type_str in int_type:
            type_str = lang["DETAILS"]["NUMBER"]
        else:
            type_str = lang["DETAILS"]["TEXT"]
        html += "<tr><td>" + j['name'] + "</td><td>" + type_str + "</td></tr>"
    else:
        html += ""
    return html

def convert_text_to_json(text):
    # //solr stores the json structure of nested elements as a smi usable string
    # // convert the string to json for use!
    # // returns a usable json object

    reg = r'(\w+)=([^\s|\[|,|\{|\}]+)'  # get words between { and = (\w+)=([^\s|\[|,|\{|\}]+)
    text = re.sub(reg, r'"\1"="\2"', text)

    # find all the {att: instances
    text = re.sub(r'({)([^"|{]*)(=)', r'{"\2"=', text)

    # and wrap the last attributes that equal something - adding back '='
    text = re.sub(r'\s([^=|"|,]*)=', r'"\1"=', text)

    # replace any empty strings =,
    text = text.replace('=,', '="",')
    # and empty slots
    text = text.replace(', ,', ',')

    # lastly replace the '=' with ':'
    text = text.replace('=', ':')

    try:
        return json.loads(text)
    except:
        return text

def get_endpoints():
   return End_Point.objects.values_list('name', 'thumbnail')

def get_publisher_icon(resource,end_points,size_class=""):
    html = ""
    for e in end_points:
       if "dct_publisher_sm" in resource:
            for p in resource["dct_publisher_sm"]:
                if p == e[0] and e[1]:
                    html += '<div class="pub_icon '+size_class+'"><img src="'+e[1]+'" title="'+e[0]+'"></div>'

    return html