import arrow
import json

from django.contrib.auth.decorators import login_required
from django.shortcuts import HttpResponse
from django.template import defaultfilters as filters
from django.utils.timezone import localtime
from django.views.decorators.cache import cache_page

from panopuppet.pano.puppetdb import puppetdb
from panopuppet.pano.puppetdb.puppetdb import get_server
from panopuppet.pano.settings import CACHE_TIME

__author__ = 'etaklar'


@login_required
@cache_page(CACHE_TIME)
def report_log_json(request, report_hash=None):
    source_url, source_certs, source_verify = get_server(request)
    # Redirects to the events page if GET param latest is true..
    context = {}

    if report_hash is None:
        context['error'] = 'Report Hash not provided.'
        return HttpResponse(json.dumps(context, indent=2), content_type="application/json")

    report_logs = puppetdb.api_get(
        api_url=source_url,
        cert=source_certs,
        verify=source_verify,
        path='/reports/' + report_hash + '/logs',
        api_version='v4',
    )
    if 'error' in report_logs:
        context = report_logs
        return HttpResponse(json.dumps(context, indent=2), content_type="application/json")

    # Remove the dict from the list...
    for log in report_logs:
        # Parse... 2015-09-18T18:02:04.753163330+02:00
        # Puppetlabs... has a super long millisecond counter (9 digits!!!)
        # We need to trim those down...
        time = log['time'][0:26] + log['time'][-6:-3] + log['time'][-2:]
        time = arrow.get(time).to('UTC').datetime
        log['time'] = filters.date(localtime(time), 'Y-m-d H:i:s')

    context['agent_log'] = report_logs
    context['report_hash'] = report_hash
    return HttpResponse(json.dumps(context, indent=2), content_type="application/json")
