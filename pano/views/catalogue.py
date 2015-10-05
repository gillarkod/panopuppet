import pytz

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.http import HttpResponseBadRequest

from pano.puppetdb.puppetdb import set_server
from pano.settings import AVAILABLE_SOURCES

__author__ = 'etaklar'


@login_required
def catalog(request):
    context = {
        'timezones': pytz.common_timezones,
        'SOURCES': AVAILABLE_SOURCES
    }

    if request.method == 'GET':
        if 'source' in request.GET:
            source = request.GET.get('source')
            set_server(request, source)
    elif request.method == 'POST':
        if 'timezone' in request.POST:
            request.session['django_timezone'] = request.POST['timezone']
            return redirect(request.POST['return_url'])
        else:
            return HttpResponseBadRequest('Invalid POST request.')

    return render(request, 'pano/catalogue.html', context)
