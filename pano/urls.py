__author__ = 'etaklar'

from django.conf.urls import patterns, url

from pano import views

urlpatterns = patterns('',
                       url(r'^$', views.splash, name='index'),
                       url(r'^login/$', views.splash, name='login'),
                       url(r'^logout/$', views.logout_view, name='logout'),
                       url(r'^dashboard/$', views.index, name='dashboard'),
                       url(r'^dashfails/$', views.indexfailed, name='dashfailed'),
                       url(r'^dashunreported/$', views.indexunreported, name='dashunreported'),
                       url(r'^dashchanged/$', views.indexchanged, name='dashchanged'),
                       url(r'^nodes/$', views.nodes, name='nodes'),
                       url(r'^reports/(?P<certname>[\w\.-]+)/$', views.reports, name='reports'),
                       url(r'^events/(?P<certname>[\w\.-]+)/(?P<hashid>[\w\.-]+)/$', views.detailed_events, name='events'),
                       url(r'^analytics/$', views.analytics, name='analytics'),
                       url(r'^facts/(?P<certname>[\w\.-]+)/$', views.facts, name='facts'),
                       )
