import csv
import datetime
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import HttpResponseBadRequest, StreamingHttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.cache import cache_page
import pytz
from pano.methods.dictfuncs import dictstatus as dictstatus
from pano.puppetdb import puppetdb
from pano.settings import CACHE_TIME
from pano.views import Echo

__author__ = 'etaklar'


@login_required
@cache_page(CACHE_TIME)
def nodes(request):
    if request.method == 'POST':
        request.session['django_timezone'] = request.POST['timezone']
        return redirect(request.POST['return_url'])
    else:
        valid_sort_fields = (
            'certname',
            'latestCatalog',
            'latestReport',
            'latestFacts',
            'success',
            'noop',
            'failure',
            'skipped')
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
                                       )
        if request.session['sortfieldby'] == 'desc':
            merged_list = dictstatus(
                node_list, report_list, sortby=request.session['sortfield'], asc=True)
            sort_field_order_opposite = 'asc'
        else:
            merged_list = dictstatus(
                node_list, report_list, sortby=request.session['sortfield'], asc=False)
            sort_field_order_opposite = 'desc'

        if dl_csv is True:
            if merged_list == []:
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

        len_nodes_results = len(merged_list)
        paginator = Paginator(merged_list, request.session['limits'])

        try:
            merged_list = paginator.page(request.session['page'])
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
            'node_list': merged_list,
            'timezones': pytz.common_timezones,
            'c_r_limit': request.session['limits'],
            'r_sfield': valid_sort_fields,
            'c_r_sfield': request.session['sortfield'],
            'r_sfieldby': ['asc', 'desc'],
            'c_r_sfieldby': request.session['sortfieldby'],
            'c_r_sfieldby_o': sort_field_order_opposite,
            'total_nodes': len_nodes_results,
            'tot_pages': paginator.page_range,
        }
        return render(request, 'pano/nodes.html', context)
