__author__ = 'etaklar'

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import HttpResponseBadRequest, HttpResponse, StreamingHttpResponse
from django.shortcuts import redirect
from django.views.decorators.cache import cache_page
import csv
import datetime
from pano.views import Echo
from pano.methods.dictfuncs import dictstatus as dictstatus
from pano.puppetdb import puppetdb
from pano.settings import CACHE_TIME
import json
from django.views.decorators.csrf import ensure_csrf_cookie


@ensure_csrf_cookie
@login_required
@cache_page(CACHE_TIME)
def nodes_json(request):
    if request.method == 'POST':
        request.session['django_timezone'] = request.POST['timezone']
        return redirect(request.POST['return_url'])
    else:
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
                avail_sortfield = ['certname', 'latestReport', 'latestCatalog', 'latestFacts', 'success', 'noop',
                                   'failure', 'skipped']
                if request.session['sortfield'] != request.GET.get('sortfield'):
                    request.session['sortfield'] = request.GET.get('sortfield')
                if request.session['sortfield'] not in avail_sortfield:
                    request.session['sortfield'] = 'latestReport'
            else:
                if 'sortfield' not in request.session:
                    request.session['sortfield'] = 'latestReport'

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
                        request.session['sortfield'] = 'latestReport'
                        request.session['sortfieldby'] = 'desc'
                        request.session['page'] = 1
                        request.session['search'] = None
                    else:
                        request.session['page'] = 1
                        request.session['search'] = request.GET.get('search')
            else:
                if 'search' not in request.session:
                    request.session['search'] = None
        except:
            return HttpResponseBadRequest('Oh no! Your filters were invalid.')

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

        node_list = puppetdb.api_get(path='/nodes',
                                     api_version='v4',
                                     params=puppetdb.mk_puppetdb_query(
                                         node_params),
                                     )
        # Work out the number of pages from the xrecords response
        # return fields that you can sort by
        valid_sort_fields = (
            'certname',
            'latestCatalog',
            'latestReport',
            'latestFacts',
            'success',
            'noop',
            'failure',
            'skipped')

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
        report_list = puppetdb.api_get(path='event-counts',
                                       params=puppetdb.mk_puppetdb_query(
                                           report_params),
                                       api_version='v4',
                                       )
        if sort_field_order == 'desc':
            merged_list = dictstatus(
                node_list, report_list, sortby=sort_field, asc=True)
            sort_field_order_opposite = 'asc'
        elif sort_field_order == 'asc':
            merged_list = dictstatus(
                node_list, report_list, sortby=sort_field, asc=False)
            sort_field_order_opposite = 'desc'
        total_results = len(merged_list)
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

        paginator = Paginator(merged_list, request.session['limits'])
        try:
            merged_list = paginator.page(page_num)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            merged_list = paginator.page(1)
        except EmptyPage:
            # If page is out of range, deliver last page
            merged_list = paginator.page(paginator.num_pages)


        """
        c_r_s* = current request sort
        c_r_* = current req
        r_s* = requests available
        """
        context = {
            'nodeList': merged_list.object_list,
            'total_nodes': total_results,
            'c_r_page': page_num,
            'c_r_limit': request.session['limits'],
            'r_sfield': valid_sort_fields,
            'c_r_sfield': sort_field,
            'r_sfieldby': ['asc', 'desc'],
            'c_r_sfieldby': sort_field_order,
            'c_r_sfieldby_o': sort_field_order_opposite,
            'tot_pages': paginator.page_range,
        }
        return HttpResponse(json.dumps(context))
