from django.urls import path
from django.urls import include, re_path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('preview/', views.preview, name='preview'),
    path('generate_gbl_record/', views.generate_gbl_record, name='generate_gbl_record'),

    path('fetch_solr', views.fetch_solr, name='fetch_solr'),

    # path('catalog', views.index, name='index'),
    # path('catalog/<resource_id>', views.resource_page, name='resource_page'),
    # path('catalog/<resource_id>/<LANG>', views.resource_page, name='resource_page'),

    # load the details alone
    path('details/<resource_id>', views.details_page, name='details_page'),
    path('details/<resource_id>/<LANG>', views.details_page, name='details_page'),
    path('admin/<resource_id>', views.resource_admin_page, name='resource_admin_page'),

    path('result/', views.result_page, name='result_page'),
    #
    # path('admin/delete/', views.resource_admin_delete_page, name='delete_page'),
    path('endpoint_details/', views.get_endpoint_details, name='get_endpoint_details'),
    path('url_types/', views.get_url_types, name='get_url_types'),
    path('services/', views.get_services, name='get_services'),
    path('suggest/', views.get_suggest, name='get_suggest'),
    path('rss/', views.get_rss, name='get_rss'),
    re_path('sr/(?P<url>.*)$', views.spoof_request, name='spoof_request'),
]


