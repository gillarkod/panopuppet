__author__ = 'etaklar'

import csv
import datetime
import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, HttpResponse, StreamingHttpResponse
from django.shortcuts import redirect

from django.views.decorators.csrf import ensure_csrf_cookie

from pano.views import Echo
from pano.methods.dictfuncs import dictstatus as dictstatus
from pano.puppetdb import puppetdb


@ensure_csrf_cookie
@login_required
def nodes_json(request):
    if request.method == 'POST':
        request.session['django_timezone'] = request.POST['timezone']
        return redirect(request.POST['return_url'])
    else:
        valid_sort_fields = (
            'certname',
            'catalog-timestamp',
            'report-timestamp',
            'facts-timestamp',
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
                    request.session['sortfield'] = 'report-timestamp'
            else:
                if 'sortfield' not in request.session:
                    request.session['sortfield'] = 'report-timestamp'

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
                        request.session['sortfield'] = 'report-timestamp'
                        request.session['sortfieldby'] = 'desc'
                        request.session['page'] = 1
                        request.session['search'] = None
                    else:
                        request.session['page'] = 1
                        request.session['search'] = request.GET.get('search')
            else:
                if 'search' not in request.session:
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

        nodes_sort_fields = ['certname', 'catalog-timestamp', 'report-timestamp', 'facts-timestamp']
        if sort_field in nodes_sort_fields:
            node_params['order-by'] = {
                'order-field':
                    {
                        'field': sort_field,
                        'order': sort_field_order,
                    },
            }
            node_params['limit'] = request.session['limits']
            node_params['offset'] = request.session['offset']
            node_params['include-total'] = 'true'
        else:
            node_params['order-by'] = {
                'order-field':
                    {
                        'field': 'report-timestamp',
                        'order': 'desc',
                    },
            }
        node_sort_fields = ['certname', 'catalog-timestamp', 'report-timestamp', 'facts-timestamp']
        if sort_field in node_sort_fields:
            node_list, node_headers = puppetdb.api_get(path='/nodes',
                                                       api_version='v4',
                                                       params=puppetdb.mk_puppetdb_query(
                                                           node_params),
                                                       )
        else:
            node_list = puppetdb.api_get(path='/nodes',
                                         api_version='v4',
                                         params=puppetdb.mk_puppetdb_query(
                                             node_params),
                                         )

        # Work out the number of pages from the xrecords response
        # return fields that you can sort by
        # for each node in the node_list, find out if the latest run has any failures
        # v3/event-counts --data-urlencode query='["=","latest-report?",true]'
        # --data-urlencode summarize-by='certname'
        report_params = {
            'query':
                {
                    1: '["and",["=","latest-report?",true],["in", "certname",["extract", "certname",["select-nodes",["null?","deactivated",true]]]]]'
                },
            'summarize-by': 'certname',
        }
        status_sort_fields = ['successes', 'failures', 'skips', 'noops']
        if sort_field in status_sort_fields:
            if request.session['search'] is not None:
                report_params['query'] = {'operator': 'and',
                                          1: request.session['search'],
                                          2: '["=","latest-report?",true]',
                                          3: '["in", "certname",["extract", "certname",["select-nodes",["null?","deactivated",true]]]]',
                                          }
            report_params['order-by'] = {
                'order-field':
                    {
                        'field': sort_field,
                        'order': sort_field_order,
                    }
            }
            report_params['limit'] = request.session['limits']
            report_params['include-total'] = 'true'
            report_params['offset'] = request.session['offset']
            report_list, report_headers = puppetdb.api_get(path='event-counts',
                                                           params=puppetdb.mk_puppetdb_query(
                                                               report_params),
                                                           api_version='v4',
                                                           )
        else:
            report_list = puppetdb.api_get(path='event-counts',
                                           params=puppetdb.mk_puppetdb_query(
                                               report_params),
                                           api_version='v4',
                                           )
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

        if sort_field_order == 'desc':
            merged_list = dictstatus(
                node_list, report_list, sortby=sort_field, asc=True, sort=False)
            sort_field_order_opposite = 'asc'
        elif sort_field_order == 'asc':
            merged_list = dictstatus(
                node_list, report_list, sortby=sort_field, asc=False, sort=False)
            sort_field_order_opposite = 'desc'

        if dl_csv is True:
            if merged_list is []:
                pass
            else:
                # Generate a sequence of rows. The range is based on the maximum number of
                # rows that can be handled by a single sheet in most spreadsheet
                # applications.
                csv_headers = ('Certname',
                               'Latest Catalog',
                               'Latest Report',
                               'Latest Facts',
                               'Success',
                               'Noop',
                               'Failure',
                               'Skipped')

                merged_list.insert(0, csv_headers)
                rows = merged_list
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
            'nodeList': merged_list,
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
        return HttpResponse(json.dumps(context))
