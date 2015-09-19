__author__ = 'etaklar'
from pano.views.analytics import analytics
from pano.views.dashboard import dashboard
from pano.views.event_analytics import event_analytics
from pano.views.filebucket import filebucket
from pano.views.logout import logout_view
from pano.views.node_facts import facts
from pano.views.nodes import nodes
from pano.views.report_events import detailed_events
from pano.views.reports import reports
from pano.views.report_agent_logs import agent_logs
from pano.views.splash import splash
from pano.views.radiator import radiator
from pano.views.api.node_data import nodes_json
from pano.views.api.fact_data import facts_json
from pano.views.api.dashboard_data import dashboard_status_json, dashboard_nodes_json, dashboard_json
from pano.views.api.report_data import reports_json
from pano.views.api.report_agent_log import report_log_json
from pano.views.api.query_filters import filter_json
from django.conf.urls import patterns, url

urlpatterns = patterns('',
                       url(r'^$', splash, name='index'),
                       url(r'^login/$', splash, name='login'),
                       url(r'^logout/$', logout_view, name='logout'),
                       url(r'^dashboard/$', dashboard, name='dashboard'),
                       url(r'^filebucket/$', filebucket, name='filebucket'),
                       url(r'^nodes/$', nodes, name='nodes'),
                       url(r'^reports/(?P<certname>[\w\.-]+)/$', reports, name='reports'),
                       url(r'^events/(?P<hashid>[\w\.-]+)/$', detailed_events, name='events'),
                       url(r'^events/(?P<certname>[\w\.-]+)/(?P<report_hash>[\w]+)/$', agent_logs, name='agent_logs'),
                       url(r'^analytics/$', analytics, name='analytics'),
                       url(r'^eventanalytics/$', event_analytics, name='event_analytics'),
                       url(r'^eventanalytics/(?P<view>[\w]+)/$', event_analytics, name='event_analytics'),
                       url(r'^facts/(?P<certname>[\w\.-]+)/$', facts, name='facts'),
                       url(r'^radiator/$', radiator, name='radiator'),
                       # API URLS
                       url(r'^api/nodes/$', nodes_json, name='api_nodes'),
                       url(r'^api/facts/$', facts_json, name='api_facts'),
                       url(r'^api/filters/$', filter_json, name='api_filter'),
                       url(r'^api/reports/(?P<certname>[\w\.-]+)/$', reports_json, name='api_reports'),
                       url(r'^api/reports/(?P<report_hash>[\w]+)/agent_log$', report_log_json, name='api_report_logs'),
                       # url(r'^api/reports/(?P<report_hash>[a-z0-9]+)/metrics$', report_metrics_json, name='api_report_metrics'),
                       url(r'^api/dashboard/$', dashboard_json, name='api_dashboard'),
                       url(r'^api/dashboard/status$', dashboard_status_json, name='api_dashboard_status'),
                       url(r'^api/status$', dashboard_status_json, name='api_dashboard_status'),
                       url(r'^api/dashboard/nodes/$', dashboard_nodes_json, name='api_dashboard_nodes'),
                       )
