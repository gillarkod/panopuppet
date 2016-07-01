import csv
import datetime
import json

import time # For debug

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, HttpResponse, StreamingHttpResponse
from django.shortcuts import redirect
from django.views.decorators.csrf import ensure_csrf_cookie

from panopuppet.pano.methods.dictfuncs import dictstatus as dictstatus
from panopuppet.pano.puppetdb import puppetdb
from panopuppet.pano.puppetdb.pdbutils import generate_csv
from panopuppet.pano.puppetdb.puppetdb import set_server, get_server
from panopuppet.pano.views import Echo

__author__ = 'etaklar'

def print_time(start_time):
    print(time.time() - start_time)

@ensure_csrf_cookie
@login_required
def nodes_json(request):

    r_st = time.time()
    if request.method == 'GET':
        if 'source' in request.GET:
            source = request.GET.get('source')
            set_server(request, source)
    if request.method == 'POST':
        request.session['django_timezone'] = request.POST['timezone']
        return redirect(request.POST['return_url'])

    source_url, source_certs, source_verify = get_server(request)
    puppet_run_time = get_server(request, type='run_time')
    valid_sort_fields = (
        'certname',
        'catalog_timestamp',
        'report_timestamp',
        'facts_timestamp',
        'successes',
        'noops',
        'failures',
        'skips')
    try:
        # If user requested to download csv formatted file. Default value is False
        dl_csv = request.GET.get('dl_csv', False)
        if dl_csv == 'true':
            dl_csv = True
        else:
            dl_csv = False
        # Add limits to session
        if request.GET.get('limits', False):
            if request.session['limits'] != int(request.GET.get('limits', 50)):
                request.session['limits'] = int(request.GET.get('limits', 50))
            if request.session['limits'] <= 0:
                request.session['limits'] = 50
        else:
            if 'limits' not in request.session:
                request.session['limits'] = 50

        # Cur Page Number
        if request.GET.get('page', False):
            if request.session['page'] != int(request.GET.get('page', 1)):
                request.session['page'] = int(request.GET.get('page', 1))
            if request.session['page'] <= 0:
                request.session['page'] = 1
        else:
            if 'page' not in request.session:
                request.session['page'] = 1

        # Cur sort field
        if request.GET.get('sortfield', False):
            if request.session['sortfield'] != request.GET.get('sortfield'):
                request.session['sortfield'] = request.GET.get('sortfield')
            if request.session['sortfield'] not in valid_sort_fields:
                request.session['sortfield'] = 'report_timestamp'
        else:
            if 'sortfield' not in request.session:
                request.session['sortfield'] = 'report_timestamp'

        # Cur sort order
        if request.GET.get('sortfieldby', False):
            avail_sortorder = ['asc', 'desc']
            if request.session['sortfieldby'] != request.GET.get('sortfieldby'):
                request.session['sortfieldby'] = request.GET.get('sortfieldby')
            if request.session['sortfieldby'] not in avail_sortorder:
                request.session['sortfieldby'] = 'desc'
        else:
            if 'sortfieldby' not in request.session:
                request.session['sortfieldby'] = 'desc'
        # Search parameters takes a valid puppetdb query string
        if request.GET.get('search', False):
            if 'search' in request.session and (request.session['search'] == request.GET.get('search')):
                pass
            else:
                if request.GET.get('search') == 'clear_rules':
                    request.session['sortfield'] = 'report_timestamp'
                    request.session['sortfieldby'] = 'desc'
                    request.session['page'] = 1
                    request.session['search'] = None
                else:
                    request.session['page'] = 1
                    request.session['search'] = request.GET.get('search')
        else:
            if 'search' not in request.session:
                request.session['sortfield'] = 'report_timestamp'
                request.session['sortfieldby'] = 'desc'
                request.session['page'] = 1
                request.session['search'] = None

        # Set offset
        request.session['offset'] = (request.session['limits'] * request.session['page']) - request.session[
            'limits']
    except:
        return HttpResponseBadRequest('Oh no! Your filters were invalid.')



    # Valid sort field that the user can search agnaist.
    sort_field = request.session['sortfield']
    sort_field_order = request.session['sortfieldby']
    page_num = request.session['page']

    if request.session['search'] is not None:
        node_params = {
            'query':
                {
                    1: request.session['search']
                },
        }
    else:
        node_params = {
            'query': {},
        }

    nodes_sort_fields = ['certname', 'catalog_timestamp', 'report_timestamp', 'facts_timestamp']
    if sort_field in nodes_sort_fields:
        node_params['order_by'] = {
            'order_field':
                {
                    'field': sort_field,
                    'order': sort_field_order,
                },
        }
        if dl_csv is False:
            node_params['limit'] = request.session['limits']
            node_params['offset'] = request.session['offset']
        node_params['include_total'] = 'true'
    else:
        node_params['order_by'] = {
            'order_field':
                {
                    'field': 'report_timestamp',
                    'order': 'desc',
                },
        }
    node_sort_fields = ['certname', 'catalog_timestamp', 'report_timestamp', 'facts_timestamp']
    print_time(r_st)
    print(puppetdb.mk_puppetdb_query(node_params, request))
    if sort_field in node_sort_fields:
        try:
            node_list, node_headers = puppetdb.api_get(
                api_url=source_url,
                cert=source_certs,
                verify=source_verify,
                path='/nodes',
                api_version='v4',
                params=puppetdb.mk_puppetdb_query(
                    node_params, request),
            )
        except:
            node_list = []
            node_headers = dict()
            node_headers['X-Records'] = 0
    else:
        node_list = puppetdb.api_get(
            api_url=source_url,
            cert=source_certs,
            verify=source_verify,
            path='/nodes',
            api_version='v4',
            params=puppetdb.mk_puppetdb_query(
                node_params, request),
        )

    print_time(r_st)

    # Create a filter part to limit the following API requests to data related to the node_list.
    # Skipt the filter completely if a large number of nodes are shown as the query tends to fail.
    if len(node_list) < 1000:
        node_filter = '["or"'
        for n in node_list:
            node_filter += ',["=","certname","%s"]' % n['certname']
        node_filter += ']'
    else:
        node_filter = '["null?", "certname", false]' # Something that fits in the query

    # Work out the number of pages from the xrecords response
    # return fields that you can sort by
    # for each node in the node_list, find out if the latest run has any failures
    # v3/event-counts --data-urlencode query='["=","latest-report?",true]'
    # --data-urlencode summarize-by='certname'
    report_params = {
        'query':
            {
                1: '["and", %s, ["=","latest_report?",true],["in", "certname",["extract", "certname",["select_nodes",["null?","deactivated",true]]]]]' % node_filter,
            },
        'summarize_by': 'certname',
    }
    status_sort_fields = ['successes', 'failures', 'skips', 'noops']

    #report_status_params = {
    #    'query':
    #        {
    #            1: '["and", %s, ["=","latest_report?",true],["in", "certname",["extract", "certname",["select_nodes",["null?","deactivated",true]]]]]' % node_filter,
    #        }
    #}
    #report_status_list = puppetdb.api_get(
    #    api_url=source_url,
    #    cert=source_certs,
    #    verify=source_verify,
    #    path='/reports',
    #    params=puppetdb.mk_puppetdb_query(report_status_params, request),
    #    api_version='v4',
    #)
    print_time(r_st)
    if sort_field in status_sort_fields:
        # I think this is just to optimize, which in unessecery with node_filter
        #if request.session['search'] is not None:
        #    report_params['query'] = {'operator': 'and',
        #                              1: request.session['search'],
        #                              2: '["=","latest_report?",true]',
        #                              3: '["in", "certname",["extract", "certname",["select_nodes",["null?","deactivated",true]]]]',
        #                              }
        report_params['order_by'] = {
            'order_field':
                {
                    'field': sort_field,
                    'order': sort_field_order,
                }
        }
        report_params['include_total'] = 'true'
        # Don't limit results if its CSV
        if dl_csv is False:
            report_params['limit'] = request.session['limits']
            report_params['offset'] = request.session['offset']

        report_list, report_headers = puppetdb.api_get(
            api_url=source_url,
            cert=source_certs,
            verify=source_verify,
            path='/event-counts',
            params=puppetdb.mk_puppetdb_query(report_params, request),
            api_version='v4',
        )
    else:
        report_list = puppetdb.api_get(
            api_url=source_url,
            cert=source_certs,
            verify=source_verify,
            path='event-counts',
            params=puppetdb.mk_puppetdb_query(report_params, request),
            api_version='v4',
        )
    print_time(r_st)
    # number of results depending on sort field.
    if sort_field in status_sort_fields:
        xrecords = report_headers['X-Records']
        total_results = xrecords
    elif sort_field in nodes_sort_fields:
        xrecords = node_headers['X-Records']
        total_results = xrecords

    num_pages_wdec = float(xrecords) / request.session['limits']
    num_pages_wodec = float("{:.0f}".format(num_pages_wdec))
    if num_pages_wdec > num_pages_wodec:
        num_pages = num_pages_wodec + 1
    else:
        num_pages = num_pages_wodec

    # Converts lists of dicts to dicts.
    #status_dict = {item['certname']: item for item in report_status_list} # /repots
    report_dict = {item['subject']['title']: item for item in report_list} # /events-count
    if sort_field_order == 'desc':
        rows = dictstatus(node_list,
                          None,
                          #status_dict,
                          report_dict,
                          sortby=sort_field,
                          asc=True,
                          sort=False,
                          puppet_run_time=puppet_run_time)
        sort_field_order_opposite = 'asc'
    elif sort_field_order == 'asc':
        rows = dictstatus(node_list,
                          None,
                          report_dict,
                          sortby=sort_field,
                          asc=False,
                          sort=False,
                          puppet_run_time=puppet_run_time)
        sort_field_order_opposite = 'desc'

    print_time(r_st)

    if dl_csv is True:
        if rows is []:
            pass
        else:
            # Generate a sequence of rows. The range is based on the maximum number of
            # rows that can be handled by a single sheet in most spreadsheet
            # applications.
            include_facts = request.GET.get('include_facts', False)
            csv_headers = ['Certname',
                           'Latest Catalog',
                           'Latest Report',
                           'Latest Facts',
                           'Success',
                           'Noop',
                           'Failure',
                           'Skipped',
                           'Run Status']
            if include_facts is not False:
                merged_list_facts = []
                facts = {}
                for fact in include_facts.split(','):
                    # Sanitize the fact input from the user
                    fact = fact.strip()
                    # Add the fact name to the headers list
                    csv_headers.append(fact)

                    # build the params for each fact.
                    facts_params = {
                        'query':
                            {
                                1: '["=","name","' + fact + '"]'
                            },
                    }
                    fact_list = puppetdb.api_get(
                        api_url=source_url,
                        cert=source_certs,
                        verify=source_verify,
                        path='facts',
                        params=puppetdb.mk_puppetdb_query(facts_params),
                        api_version='v4',
                    )
                    # Populate the facts dict with the facts we have retrieved
                    # Convert the fact list into a fact dict!
                    facts[fact] = {item['certname']: item for item in fact_list}

                i = 1
                jobs = {}
                # Add ID to each job so that it can be assembled in
                # the same order after we recieve the job results
                # We do this via jobs so that we can get faster results.
                for node in rows:
                    jobs[i] = {
                        'id': i,
                        'include_facts': include_facts.split(','),
                        'node': node,
                        'facts': facts,
                    }
                    i += 1

                csv_results = generate_csv(jobs)
                rows = []
                i = 1
                # with the job results we can now recreate merged_list
                # in the order we sent them.
                while i <= len(csv_results):
                    rows.append(csv_results[i])
                    i += 1
            # Insert the csv header to the top of the list.
            rows.insert(0, csv_headers)
            pseudo_buffer = Echo()
            writer = csv.writer(pseudo_buffer)
            response = StreamingHttpResponse((writer.writerow(row) for row in rows),
                                             content_type="text/csv")
            response['Content-Disposition'] = 'attachment; filename="puppetdata-%s.csv"' % (datetime.datetime.now())
            return response

    """
    c_r_s* = current request sort
    c_r_* = current req
    r_s* = requests available
    """
    context = {
        'nodeList': rows,
        'total_nodes': total_results,
        'c_r_page': page_num,
        'c_r_limit': request.session['limits'],
        'r_sfield': valid_sort_fields,
        'c_r_sfield': sort_field,
        'r_sfieldby': ['asc', 'desc'],
        'c_r_sfieldby': sort_field_order,
        'c_r_sfieldby_o': sort_field_order_opposite,
        'tot_pages': '{0:g}'.format(num_pages),
    }
    return HttpResponse(json.dumps(context), content_type="application/json")


def search_nodes_json(request):
    source_url, source_certs, source_verify = get_server(request)
    if request.method == 'GET':
        if 'search' in request.GET:
            search = request.GET.get('search')

    # Create a search regex for certname spelt with below.
    nodes_params = {
        'query':
            {
                1: '["~","certname","' + search + '"]'
            },
        'order_by':
            {
                'order_field':
                    {
                        'field': 'certname',
                        'order': 'desc',
                    },
            },
        # 'limit': 25,
    }
    nodes_list = puppetdb.api_get(
        api_url=source_url,
        cert=source_certs,
        verify=source_verify,
        path='/nodes',
        api_version='v4',
        params=puppetdb.mk_puppetdb_query(
            nodes_params, request),
    )
    return HttpResponse(json.dumps(nodes_list, indent=2), content_type="application/json")
