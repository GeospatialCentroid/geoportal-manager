from django.shortcuts import render
from resources.models import Resource,Community_Input

from django.views.decorators.csrf import csrf_exempt

from django.http import HttpResponse, HttpResponseRedirect
from django.core.serializers.json import DjangoJSONEncoder

from django.contrib.gis.geos import GEOSGeometry
import urllib.request, json

from django.conf import settings

# Create your views here.
def geo_reference(request):
    # for loading relative items dynamically
    args = {'STATIC_URL': settings.STATIC_URL}
    resource_id=request.GET.get('id')

    args["id"]=resource_id[0:resource_id.rfind("-")]

    return render(request, 'geo_reference/index.html', args)


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