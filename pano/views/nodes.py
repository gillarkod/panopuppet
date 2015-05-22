from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.views.decorators.cache import cache_page
import pytz

from pano.settings import CACHE_TIME


__author__ = 'etaklar'


@login_required
def nodes(request):
    if request.method == 'POST':
        request.session['django_timezone'] = request.POST['timezone']
        return redirect(request.POST['return_url'])
    else:
        context = {
            'timezones': pytz.common_timezones,
        }
        return render(request, 'pano/nodes.html', context)
