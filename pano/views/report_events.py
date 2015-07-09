__author__ = 'etaklar'
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.cache import cache_page
from pano.puppetdb import puppetdb
from pano.puppetdb.pdbutils import json_to_datetime
from pano.settings import CACHE_TIME
from pano.puppetdb.puppetdb import set_server, get_server
from pano.settings import AVAILABLE_SOURCES
import pytz


@login_required
@cache_page(CACHE_TIME * 60)  # Cache for cache_time multiplied 60 because the report will never change...
def detailed_events(request, hashid=None):
    context = {'timezones': pytz.common_timezones,
               'SOURCES': AVAILABLE_SOURCES}
    if request.method == 'GET':
        if 'source' in request.GET:
            source = request.GET.get('source')
            set_server(request, source)
    if request.method == 'POST':
        request.session['django_timezone'] = request.POST['timezone']
        return redirect(request.POST['return_url'])

    source_url, source_certs, source_verify = get_server(request)
    report_timestamp = request.GET.get('report_timestamp')
    events_params = {
        'query':
            {
                1: '["=","report","' + hashid + '"]'
            },
        'order-by':
            {
                'order-field':
                    {
                        'field': 'timestamp',
                        'order': 'asc',
                    },
                'query-field': {'field': 'certname'},
            },
    }
    events_list = puppetdb.api_get(
        api_url=source_url,
        cert=source_certs,
        verify=source_verify,
        path='/events',
        api_version='v4',
        params=puppetdb.mk_puppetdb_query(events_params),
    )
    environment = ''
    certname = ''
    event_execution_times = []
    sorted_events = None
    last_event_time = None
    last_event_title = None
    run_end_time = None

    if len(events_list) != 0:
        single_event = events_list[0]
        environment = single_event['environment']
        certname = single_event['certname']
        for event in events_list:
            event_title = event['resource-title']
            event_start_time = json_to_datetime(event['timestamp'])
            if last_event_time is None and last_event_title is None:
                last_event_time = event_start_time
                last_event_title = event_title
                run_end_time = json_to_datetime(event['run-end-time'])
                continue
            else:
                event_exec_time = (event_start_time - last_event_time).total_seconds()
                add_event = (last_event_title, event_exec_time)
                event_execution_times.append(add_event)
                last_event_time = event_start_time
                last_event_title = event_title
        event_exec_time = (last_event_time - run_end_time).total_seconds()
        add_event = [last_event_title, event_exec_time]
        event_execution_times.append(add_event)
        sorted_events = sorted(event_execution_times, reverse=True, key=lambda field: field[1])
        if len(sorted_events) > 10:
            sorted_events = sorted_events[:10]
    else:
        events_list = False
    context['certname'] = certname
    context['report_timestamp'] = report_timestamp
    context['hashid'] = hashid
    context['events_list'] = events_list
    context['event_durations'] = sorted_events
    context['environment'] = environment

    return render(request, 'pano/detailed_events.html', context)
