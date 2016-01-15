import pytz

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.cache import cache_page

from panopuppet.pano.puppetdb.puppetdb import set_server
from panopuppet.pano.settings import AVAILABLE_SOURCES, CACHE_TIME

__author__ = 'etaklar'


@login_required
@cache_page(CACHE_TIME)
def dashboard(request):
    context = {'timezones': pytz.common_timezones,
               'SOURCES': AVAILABLE_SOURCES}
    if request.method == 'GET':
        if 'source' in request.GET:
            source = request.GET.get('source')
            set_server(request, source)
    if request.method == 'POST':
        request.session['django_timezone'] = request.POST['timezone']
        return redirect(request.POST['url'])

    return render(request, 'pano/dashboard.html', context)
