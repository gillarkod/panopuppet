from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.cache import cache_page
from pano.puppetdb import puppetdb
from pano.settings import CACHE_TIME
from pano.puppetdb.puppetdb import set_server, get_server
from pano.settings import AVAILABLE_SOURCES, NODES_DEFAULT_FACTS
import pytz

__author__ = 'etaklar'


@login_required
@cache_page(CACHE_TIME)
def reports(request, certname=None):
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
    # Redirects to the events page if GET param latest is true..
    if request.GET.get('latest', False):
        if request.GET.get('latest') == "true":
            request.session['report_page'] = 1
            latest_report_params = {
                'query':
                    {
                        1: '["=","certname","' + certname + '"]'
                    },
                'order_by':
                    {
                        'order_field':
                            {
                                'field': 'start_time',
                                'order': 'desc',
                            },
                    },
                'limit': 1,
            }
            latest_report = puppetdb.api_get(
                api_url=source_url,
                cert=source_certs,
                verify=source_verify,
                path='/reports',
                api_version='v4',
                params=puppetdb.mk_puppetdb_query(latest_report_params, request),
            )
            report_hash = ""
            # If latest reports do not exist, send to the nodes page
            # Should only occur if the user is trying to hax their way
            # into a node without having the correct permission
            if latest_report:
                for report in latest_report:
                    report_env = report['environment']
                    report_hash = report['hash']
                return redirect('/pano/events/' + report_hash + '?report_timestamp=' + request.GET.get(
                    'report_timestamp') + '&envname=' + report_env)
            else:
                return redirect('/pano/nodes/')

    if certname != request.session.get('last_shown_node', ''):
        request.session['last_shown_node'] = certname
        request.session['report_page'] = 1

    context['certname'] = certname
    context['node_facts'] = ','.join(NODES_DEFAULT_FACTS)

    return render(request, 'pano/reports.html', context)
