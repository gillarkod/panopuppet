__author__ = 'etaklar'
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.http import HttpResponseBadRequest
from pano.puppetdb.puppetdb import set_server
from pano.settings import AVAILABLE_SOURCES
import pytz
from pano.models import SavedQueries


@login_required
def nodes(request):
    results = SavedQueries.objects.filter(username=request.user.get_username())
    if not results.exists():
        results = False
    context = {'timezones': pytz.common_timezones,
               'SOURCES': AVAILABLE_SOURCES,
               'saved_queries': results}
    if request.method == 'GET':
        if 'source' in request.GET:
            source = request.GET.get('source')
            set_server(request, source)
        elif 'load_query' in request.GET:
            request.session['search'] = request.GET.get('load_query', request.session['search'])
            return redirect('nodes')
    elif request.method == 'POST':
        if 'timezone' in request.POST:
            request.session['django_timezone'] = request.POST['timezone']
            return redirect(request.POST['return_url'])
        else:
            return HttpResponseBadRequest('Invalid POST request.')

    return render(request, 'pano/nodes.html', context)
