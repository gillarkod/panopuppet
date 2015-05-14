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
        try:
            limits = int(request.GET.get('limits', 50))
            if limits <= 0:
                limits = 50
            sort_field = str(request.GET.get('sortfield', 'latestReport'))
            sort_field_order = str(request.GET.get('sortfieldby', 'desc'))
            page_num = int(request.GET.get('page', 1))
            # Search parameters takes a valid puppetdb query string
            search_node = request.GET.get('search', None)
            # If user requested to download csv formatted file. Default value is False
            dl_csv = request.GET.get('dl_csv', False)
            if dl_csv == 'true':
                dl_csv = True
            else:
                dl_csv = False
        except:
            return HttpResponseBadRequest('Oh no! Your filters were invalid.')

        if search_node is not None:
            node_params = {
                'query':
                    {
                        1: search_node
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
        if sort_field_order == 'desc':
            merged_list = dictstatus(
                node_list, report_list, sortby=sort_field, asc=True)
            sort_field_order_opposite = 'asc'
        else:
            merged_list = dictstatus(
                node_list, report_list, sortby=sort_field, asc=False)
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
        paginator = Paginator(merged_list, limits)

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
            'node_list': merged_list,
            'timezones': pytz.common_timezones,
            'c_r_limit': request.GET.get('limits', 50),
            'r_sfield': valid_sort_fields,
            'c_r_sfield': sort_field,
            'r_sfieldby': ['asc', 'desc'],
            'c_r_sfieldby': sort_field_order,
            'c_r_sfieldby_o': sort_field_order_opposite,
            'tot_pages': paginator.page_range,
        }
        return render(request, 'pano/nodes.html', context)
