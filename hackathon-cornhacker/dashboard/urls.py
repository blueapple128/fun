from django.conf.urls import url

from . import views

urlpatterns = [
  url(r'^$', views.dashboard, name='dashboard'),
  url(r'^(?P<id>[0-9]+)/$', views.info, name='info'),
  url(r'^placeholder/$', views.placeholder, name='placeholder'),
]

