__author__ = 'etaklar'
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_list_or_404
from django.http import HttpResponseBadRequest, HttpResponse
from django.views.decorators.cache import cache_page
from pano.settings import CACHE_TIME
import json
from pano.models import SavedQueries


@login_required
@cache_page(CACHE_TIME)
def filter_json(request):
    context = {}
    username = request.user.get_username()
    if request.method == 'POST':
        u_filter = request.POST.get('puppetdb_filter', False)
        if u_filter:
            SavedQueries.objects.create(username=username, filter=u_filter)
            return HttpResponse('Saved Filter')
        else:
            return HttpResponseBadRequest('Invalid request for filter API.')
    elif request.method == 'GET':
        user_filters = get_list_or_404(SavedQueries, username=username)
        print(user_filters)
