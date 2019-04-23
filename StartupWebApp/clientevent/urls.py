from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('pageview', views.pageview, name='pageview'),
    path('ajaxerror', views.ajaxerror, name='ajaxerror'),
    path('buttonclick', views.buttonclick, name='buttonclick'),
    path('linkevent', views.linkevent, name='linkevent'),
]