from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('geo_reference', views.geo_reference, name='geo_reference'),
    path('set_geo_reference', views.set_geo_reference, name='set_geo_reference'),
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

]


