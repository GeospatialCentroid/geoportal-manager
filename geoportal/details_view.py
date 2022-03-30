
from django.conf import settings

from . import views
from . import utils

from datetime import datetime




def get_details_args(result_data,_LANG,is_sub=False,base_url=False):
    args = {'STATIC_URL': settings.STATIC_URL}

    # dynamically load the LANG or set the default

    args['LANG'] = utils.get_lang(_LANG)


    # return render(request, 'resource/index.html', context)
    args['data'] = result_data
    if len(result_data['response']['docs'])==0:
        return

    d = result_data['response']['docs'][0]

    args['resource_id'] = d['dct_identifier_sm']
    if is_sub:
        args['sub_title'] = d['dct_title_s']
    else:
        args['title'] = d['dct_title_s']

    args['desc'] = ""
    if 'dct_description_sm' in d:
        if type(d['dct_description_sm'])==list:
            d['dct_description_sm']=d['dct_description_sm'][0]
        args['desc'] = d['dct_description_sm']

    args['thumb'] = ""
    if 'thumbnail_path_ss' in d:
        args['thumb'] = d['thumbnail_path_ss']

    args['producer_html'] = ""
    if "dct_creator_sm" in d:
        l = []
        for c in d['dct_creator_sm']:
            l.append(get_filter_link('dct_creator_sm',c,False,True))
        args['producer_html'] = ", ".join(l)
        args['producer'] = ", ".join(d['dct_creator_sm'])

    if 'locn_geometry' in d:
        args['bbox'] = d['locn_geometry']

    args['publisher_html'] = ""
    args['publisher'] = ""

    if 'dct_issued_s' in d:
        try :
            args['published'] = datetime.strptime(d['dct_issued_s'], '%Y-%m-%dT%H:%M:%SZ')
        except:
            args['published'] =d['dct_issued_s']



    if 'dct_publisher_sm' in d:
        l = []
        args['publisher'] = ", ".join(d['dct_publisher_sm'])
        for c in d['dct_publisher_sm']:
            l.append(get_filter_link('dct_publisher_sm', c,False,True))

        args['publisher_html'] = ", ".join(l)

    args['type'] = ""
    if 'gbl_resourceType_sm' in d:
        args['type'] = get_filter_link('gbl_resourceType_sm', d['gbl_resourceType_sm'],False,True)


    # allow users to georeference_link_html
    image_link=None
    if 'dct_references_s' in d:
        image_link=utils.get_ref_link(d['dct_references_s'],'image')
    if image_link and 'locn_geometry' not in d:
        iiif_link = utils.get_ref_link(d['dct_references_s'], 'iiif')
        # https://fchc.contentdm.oclc.org/digital/api/singleitem/image/pdf/hm/1404/default.png
        link="/geo_reference?id="+str(d['dct_identifier_sm'])+"&img="+image_link+"&lng=-98.74&lat=36.25&z=8"
        if iiif_link:
            link+="&iiif="+iiif_link
        args['georeference_link_html']='<a href="'+link+'" target="_blank">'+ args['LANG']["DETAILS"]["GEOREFERENCE"]+'</a><br/><br/>'



    # get the add button
    args['toggle_but_html'] = utils.get_toggle_but_html(d,args['LANG'])

    # generate the download links
    args['download_link_html'] = None
    download_link = None
    if 'dct_references_s' in d:
        download_link = utils.get_ref_link(d['dct_references_s'], "download")
    if download_link:
        print(download_link, type(download_link), "download_link")
        if  isinstance(download_link, list) and len(download_link) > 1:
            html = "<select class='form-control btn btn-primary' onchange='download_manager.download_select(this)'>"
            html += "<option selected value='0'>" + args['LANG']["DOWNLOAD"]["DOWNLOAD_BUT"] + "</option>"


            for l in download_link:
                if 'url' in l:
                    url = l["url"]
                else:
                    url = str(l)

                label = None
                if 'label' in l:
                    label = l["label"]
                elif url.find(".") > -1:
                    label = url[url.rindex('.') + 1:].upper()

                if label is not None and url is not None:
                    html += "<option value='" + url + "'>" + label + "</option>"
            html += "</select>"
        else:
            if isinstance(download_link, list):
                download_link = download_link[0]
            if isinstance(download_link, dict):
                download_link = download_link['url']
            # todo - call this through download method to support esri bundling of download
            html = '<button type="button" class="btn btn-primary" onclick="window.open(\'' + download_link + '\')">' + \
                   args['LANG']["DOWNLOAD"]["DOWNLOAD_BUT"] + '</button>'
        args['download_link_html'] = html

    # create nav
    # if we have the item count don't worry about it.
    all_records = views.get_solr_data("q=*:*&fl=id&rows=1421747930")
    if all_records is not None:
        # find out where we're at
        ds = all_records['response']['docs']
        args['num_found'] = all_records['response']['numFound']
        for i in range(len(ds)):
            if ds[i]['id'] == str(args["resource_id"]):
                if i>0:
                    prev_resource_data = utils.get_reference_data(ds[i - 1]['id'])
                    args['prev_resource_url'] = utils.get_catelog_url(prev_resource_data['response']['docs'][0])
                if i <  args['num_found'] and len(ds)>i+1:
                    # load the resource to generate the appropriate link
                    next_resource_data= utils.get_reference_data(ds[i + 1]['id'])
                    args['next_resource_url'] = utils.get_catelog_url(next_resource_data['response']['docs'][0])

                args['cur_num'] = i+1

                break

    args['pub_icon'] = utils.get_publisher_icon(d, utils.get_endpoints(),"pub_icon_med")

    args['get_catelog_link_html'] = utils.get_catelog_link_html(d, args['LANG'])
    args['get_more_details_link_html'] = utils.get_more_details_link_html(d, args['LANG'])

    args['get_catelog_html'] = utils.get_catelog_url(d)

    args['attribute_html'] = ""

    if "fields" in d:
        args['attribute_html'] = '<span class="font-weight-bold">'+args['LANG']["DETAILS"]["ATTRIBUTES"]+':</span><br/>'

        args['attribute_html'] += utils.get_fields_html(d["fields"], args['LANG'])

    args['format'] = ""
    if "dct_format_s" in d:
        args['format'] =d["dct_format_s"]

    if base_url:
        args['get_catelog_html'] = base_url+ args['get_catelog_html']

    if "dct_rights_sm" in d:
        if type(d["dct_rights_sm"])==list:
            d["dct_rights_sm"] =d["dct_rights_sm"][0]
        args['rights'] = d["dct_rights_sm"]
    return args



def get_filter_link(facet,val,replace=False,no_class=False):
    css_class = "list-group-item d-flex justify-content-between align-items-center lil_pad"
    if no_class:
        css_class=""
    # todo support multiple
    if type(val) == list:
        val= val[0]

    return "<a onclick=\"filter_manager.add_filter('"+facet+"','"+val+"',"+str(replace).lower()+")\" href = \"javascript: void(0)\" class =\""+css_class+"\">"+val+"</a>"



