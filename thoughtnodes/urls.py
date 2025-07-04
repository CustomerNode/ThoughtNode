from django.urls import path
from . import views

app_name = 'thoughtnodes'

urlpatterns = [
    path('',views.thoughtnodes_list,name='thoughtnodeslist'),
    path('addthoughtnode/',views.thoughtnode_add,name='addthoughtnode'),
    path('<slug:slug>',views.thoughtnode_view,name='viewthoughtnode'),
    path('<slug:slug>/edit/',views.thoughtnode_edit,name='editthoughtnode'),
    path('<slug:slug>/delete/',views.thoughtnode_delete,name='deletethoughtnode'),
    path('<slug:slug>/run/',views.thoughtnode_run,name='runthoughtnode'),
]