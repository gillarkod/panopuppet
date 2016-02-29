import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, HttpResponse
from django.shortcuts import get_list_or_404, redirect
from django.views.decorators.cache import cache_page

from panopuppet.pano.models import SavedQueries
from panopuppet.pano.settings import CACHE_TIME

__author__ = 'etaklar'


@login_required
@cache_page(CACHE_TIME)
def filter_json(request):
    username = request.user.get_username()
    if request.method == 'POST':
        u_filter = request.POST.get('puppetdb_filter', False)
        u_identifier = request.POST.get('identifier', False)
        if u_filter and u_identifier:
            SavedQueries.objects.create(username=username, filter=u_filter, identifier=u_identifier)
            return HttpResponse('Saved Filter')
        else:
            return HttpResponseBadRequest('Invalid request for filter API.')
    elif request.method == 'GET':
        delete_query_id = request.GET.get('delete_query', False)
        if delete_query_id:
            delete_query_id = int(delete_query_id)
            SavedQueries.objects.filter(id=delete_query_id, username=request.user.get_username()).delete()
            return redirect(request.GET.get('next_url', '/'))
        else:
            user_filters = get_list_or_404(SavedQueries, username=username)
            filters = {}
            for user_filter in user_filters:
                filters[user_filter.identifier] = user_filter.filter
            return HttpResponse(json.dumps(filters, indent=2))
