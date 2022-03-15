
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

    args['resource_id'] = d['dc_identifier_s']
    if is_sub:
        args['sub_title'] = d['dc_title_s']
    else:
        args['title'] = d['dc_title_s']

    args['desc'] = ""
    if 'dc_description_s' in d:
        args['desc'] = d['dc_description_s']

    args['thumb'] = ""
    if 'thumbnail_path_ss' in d:
        args['thumb'] = d['thumbnail_path_ss']

    args['producer_html'] = ""
    if "dc_creator_sm" in d:
        l = []
        for c in d['dc_creator_sm']:
            l.append(get_filter_link('dc_creator_sm',c,False,True))
        args['producer_html'] = ", ".join(l)
        args['producer'] = ", ".join(d['dc_creator_sm'])

    if 'solr_geom' in d:
        args['bbox'] = d['solr_geom']

    args['publisher_html'] = ""
    args['publisher'] = ""
    args['published'] = ""

    if 'dct_issued_s' in d:
        args['published'] = datetime.strptime(d['dct_issued_s'], '%Y-%m-%dT%H:%M:%SZ')


    if 'dc_publisher_sm' in d:
        l = []
        args['publisher'] = ", ".join(d['dc_publisher_sm'])
        for c in d['dc_publisher_sm']:
            l.append(get_filter_link('dc_publisher_sm', c,False,True))

        args['publisher_html'] = ", ".join(l)

    args['type'] = ""
    if 'layer_geom_type_s' in d:
        args['type'] = get_filter_link('layer_geom_type_s', d['layer_geom_type_s'],False,True)


    # allow users to georeference_link_html
    image_link=utils.get_ref_link(d['dct_references_s'],'image')
    if image_link and 'solr_geom' not in d:

        # https://fchc.contentdm.oclc.org/digital/api/singleitem/image/pdf/hm/1404/default.png
        link="/geo_reference?id="+str(d['dc_identifier_s'])+"&img="+image_link+"&lng=-98.74&lat=36.25&z=8"
        args['georeference_link_html']='<a href="'+link+'" target="_blank">'+ args['LANG']["DETAILS"]["GEOREFERENCE"]+'</a><br/><br/>'



    # get the add button
    args['toggle_but_html'] = utils.get_toggle_but_html(d,args['LANG'])

    # generate the download links
    args['download_link_html'] = None
    print(d['dct_references_s'])
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
    all_records = views.get_solr_data("q=*:*&fl=layer_slug_s&rows=1421747930")
    if all_records is not None:
        # find out where we're at
        ds = all_records['response']['docs']
        args['num_found'] = all_records['response']['numFound']
        for i in range(len(ds)):
            if ds[i]['layer_slug_s'] == str(args["resource_id"]):
                if i>0:
                    prev_resource_data = utils.get_reference_data(ds[i - 1]['layer_slug_s'])
                    args['prev_resource_url'] = utils.get_catelog_url(prev_resource_data['response']['docs'][0])
                if i <  args['num_found'] and len(ds)>i+1:
                    # load the resource to generate the appropriate link
                    next_resource_data= utils.get_reference_data(ds[i + 1]['layer_slug_s'])
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
    if "dc_format_s" in d:
        args['format'] =d["dc_format_s"]

    if base_url:
        args['get_catelog_html'] = base_url+ args['get_catelog_html']
    return args



def get_filter_link(facet,val,replace=False,no_class=False):
    css_class = "list-group-item d-flex justify-content-between align-items-center lil_pad"
    if no_class:
        css_class=""
    return "<a onclick=\"filter_manager.add_filter('"+facet+"','"+val+"',"+str(replace).lower()+")\" href = \"javascript: void(0)\" class =\""+css_class+"\">"+val+"</a>"



