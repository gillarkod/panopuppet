import pytz

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.cache import cache_page

from pano.methods import events
from pano.puppetdb.puppetdb import set_server
from pano.settings import AVAILABLE_SOURCES, CACHE_TIME

__author__ = 'etaklar'


@login_required
@cache_page(CACHE_TIME)
def event_analytics(request, view='summary'):
    context = {'timezones': pytz.common_timezones,
               'SOURCES': AVAILABLE_SOURCES}
    if request.method == 'GET':
        if 'source' in request.GET:
            source = request.GET.get('source')
            set_server(request, source)
    if request.method == 'POST':
        request.session['django_timezone'] = request.POST['timezone']
        return redirect(request.POST['return_url'])

    summary = events.get_events_summary(timespan='latest', request=request)
    context['summary'] = summary
    # Show Classes
    if request.GET.get('value', False):
        if view == 'classes':
            class_name = request.GET.get('value')
            title = "Class: %s" % class_name
            class_events = events.get_report(key='containing_class', value=class_name, request=request)
            context['events'] = class_events
        # Show Nodes
        elif view == 'nodes':
            node_name = request.GET.get('value')
            title = "Node: %s" % node_name
            node_events = events.get_report(key='certname', value=node_name, request=request)
            context['events'] = node_events
        # Show Resources
        elif view == 'resources':
            resource_name = request.GET.get('value')
            title = "Resource: %s" % resource_name
            resource_events = events.get_report(key='resource_title', value=resource_name, request=request)
            context['events'] = resource_events
        # Show Types
        elif view == 'types':
            type_name = request.GET.get('value')
            title = "Type: %s" % type_name
            type_events = events.get_report(key='resource_type', value=type_name, request=request)
            context['events'] = type_events
    # Show summary if none of the above matched
    else:
        sum_avail = ['classes', 'nodes', 'resources', 'types']
        stat_avail = ['failed', 'noop', 'success', 'skipped'
                                                   '']
        show_summary = request.GET.get('show_summary', 'classes')
        show_status = request.GET.get('show_status', 'failed')
        if show_summary in sum_avail and show_status in stat_avail:
            title = "%s with status %s" % (show_summary.capitalize(), show_status.capitalize())
            context['show_title'] = title
        else:
            title = 'Failed Classes'
            context['show_title'] = title
        return render(request, 'pano/analytics/events_details.html', context)
    # Add title to context
    context['show_title'] = title
    # if the above went well and did not reach the else clause we can also return the awesome.
    return render(request, 'pano/analytics/events_inspect.html', context)
