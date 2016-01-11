import pytz

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.cache import cache_page

from pano.puppetdb import puppetdb
from pano.puppetdb.puppetdb import set_server, get_server
from pano.settings import AVAILABLE_SOURCES, CACHE_TIME

__author__ = 'etaklar'


@login_required
@cache_page(CACHE_TIME)
def facts(request, certname=None):
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
    facts_params = {
        'query':
            {
                1: '["=","certname","' + certname + '"]'
            },
    }
    facts_list = puppetdb.api_get(
        api_url=source_url,
        cert=source_certs,
        verify=source_verify,
        path='facts',
        params=puppetdb.mk_puppetdb_query(
            facts_params, request),
    )
    context['certname'] = certname
    context['facts_list'] = facts_list

    return render(request, 'pano/facts.html', context)
