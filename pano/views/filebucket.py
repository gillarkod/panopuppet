from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
import pytz
from pano.methods.filebucket import get_file as get_filebucket

__author__ = 'etaklar'


@login_required
def filebucket(request):
    certname = request.GET.get('certname', False)
    rtype = request.GET.get('rtype', False)
    rtitle = request.GET.get('rtitle', False)
    md5_sum_from = request.GET.get('md5_from', False)
    env = request.GET.get('environment', False)
    file_status = request.GET.get('file_status', 'from')

    md5_sum_to = request.GET.get('md5_to', False)
    diff_files = request.GET.get('diff', False)
    if diff_files is not False:
        diff_files = True

    # If got md5_sum_from
    if certname and md5_sum_from and env and rtitle and rtype and file_status == 'from':
        filebucket_file = get_filebucket(request=request, certname=certname, environment=env, rtitle=rtitle,
                                         rtype=rtype,
                                         file_status=file_status,
                                         md5sum_from=md5_sum_from)
        if filebucket_file:
            context = {
                'timezones': pytz.common_timezones,
                'certname': certname,
                'content': filebucket_file,
                'isdiff': diff_files,
            }
            return render(request, 'pano/filebucket.html', context)
        else:
            return HttpResponse('Could not find file with MD5 Hash: %s in filebucket.' % (md5_sum_from))
    # If got md5_sum_to
    elif certname and md5_sum_to and env and rtitle and rtype and file_status == 'to':
        filebucket_file = get_filebucket(request=request, certname=certname, environment=env, rtitle=rtitle,
                                         rtype=rtype,
                                         file_status=file_status,
                                         md5sum_to=md5_sum_to)
        if filebucket_file:
            context = {
                'timezones': pytz.common_timezones,
                'certname': certname,
                'content': filebucket_file,
                'isdiff': diff_files,
            }
            return render(request, 'pano/filebucket.html', context)
        else:
            return HttpResponse('Could not find file with MD5 Hash: %s in filebucket.' % (md5_sum_from))
    elif certname and md5_sum_to and md5_sum_from and env and rtitle and rtype and file_status == 'both' and diff_files:
        filebucket_file = get_filebucket(request=request, certname=certname, environment=env, rtitle=rtitle,
                                         rtype=rtype,
                                         file_status=file_status,
                                         md5sum_to=md5_sum_to,
                                         md5sum_from=md5_sum_from,
                                         diff=diff_files)
        context = {
            'certname': certname,
            'content': filebucket_file,
            'isdiff': diff_files
        }

        return render(request, 'pano/filebucket.html', context)
    else:
        return HttpResponse('No valid GET params was sent.')
