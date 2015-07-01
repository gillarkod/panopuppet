__author__ = 'etaklar'
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from pano.puppetdb.puppetdb import set_server
from pano.settings import AVAILABLE_SOURCES
import pytz


@login_required
def nodes(request):
    context = {'timezones': pytz.common_timezones,
               'SOURCES': AVAILABLE_SOURCES}
    if request.method == 'GET':
        if 'source' in request.GET:
            source = request.GET.get('source')
            set_server(request, source)
    if request.method == 'POST':
        request.session['django_timezone'] = request.POST['timezone']
        return redirect(request.POST['return_url'])

    return render(request, 'pano/nodes.html', context)
