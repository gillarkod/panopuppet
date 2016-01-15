import pytz

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.cache import cache_page

from panopuppet.pano.puppetdb import puppetdb
from panopuppet.pano.puppetdb.puppetdb import set_server, get_server
from panopuppet.pano.settings import AVAILABLE_SOURCES, CACHE_TIME, NODES_DEFAULT_FACTS

__author__ = 'etaklar'


@login_required
@cache_page(CACHE_TIME)
def radiator(request, certname=None):
    context = {'timezones': pytz.common_timezones,
               'SOURCES': AVAILABLE_SOURCES}
    if request.method == 'GET':
        if 'source' in request.GET:
            source = request.GET.get('source')
            set_server(request, source)
    if request.method == 'POST':
        request.session['django_timezone'] = request.POST['timezone']
        return redirect(request.POST['return_url'])

    context['certname'] = certname
    context['node_facts'] = ','.join(NODES_DEFAULT_FACTS)

    return render(request, 'pano/radiator.html', context)
