from django.contrib.auth import logout
from django.http import HttpResponseRedirect

__author__ = 'etaklar'


def logout_view(request):
    logout(request)
    return HttpResponseRedirect("/pano/dashboard")
