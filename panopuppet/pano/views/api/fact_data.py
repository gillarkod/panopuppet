import json
import re

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, HttpResponse
from django.views.decorators.cache import cache_page

from panopuppet.pano.puppetdb import puppetdb
from panopuppet.pano.puppetdb.puppetdb import set_server, get_server
from panopuppet.pano.settings import CACHE_TIME

__author__ = 'etaklar'


@login_required
@cache_page(CACHE_TIME)
def facts_json(request):
    context = {}
    if request.method == 'GET':
        if 'source' in request.GET:
            source = request.GET.get('source')
            set_server(request, source)
    if request.method == 'POST':
        request.session['django_timezone'] = request.POST['timezone']
        return redirect(request.POST['return_url'])

    source_url, source_certs, source_verify = get_server(request)

    certname = None
    facts = None
    if 'certname' in request.GET:
        certname = request.GET.get('certname')
    if 'facts' in request.GET:
        facts = request.GET.get('facts').split(',')

    if not certname:
        context['error'] = 'Certname not specified.'
        return HttpResponse(json.dumps(context))
    if facts:
        # validate string for illegal chars
        fact_query = list()
        for fact in facts:
            fact = fact.strip()
            # Match for characters that are not a-Z or 0-9 or _
            # if theres a match illegal chars exist...
            regex = re.compile(r'[^aA-zZ0-9_]')
            matches = regex.findall(fact)
            if matches:
                context['error'] = 'Illegal characters found in facts list. '
                context['error'] += 'Facts must not match anything withddd this regex <[^aA-zZ0-9_]>.'
                return HttpResponse(json.dumps(context))
            fact_query.append('["=","name","' + fact + '"]')
        fact_query = ','.join(fact_query)
        facts_params = {
            'query':
                {
                    1: '["and",["=","certname","' + certname + '"],["or",' + fact_query + ']]'
                },
            'order-by':
                {
                    'order_field':
                        {
                            'field': 'name',
                            'order': 'asc',
                        }
                }
        }
    else:
        facts_params = {
            'query':
                {
                    1: '["=","certname","' + certname + '"]'
                },
            'order_by':
                {
                    'order_field':
                        {
                            'field': 'name',
                            'order': 'asc',
                        }
                }
        }
    facts_list = puppetdb.api_get(
        api_url=source_url,
        cert=source_certs,
        verify=source_verify,
        path='facts',
        params=puppetdb.mk_puppetdb_query(
            facts_params, request),
    )
    print(facts_list)
    context['certname'] = certname
    context['facts_list'] = facts_list

    return HttpResponse(json.dumps(context, indent=2), content_type="application/json")
