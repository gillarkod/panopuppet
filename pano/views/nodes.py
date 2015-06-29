from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from pano.puppetdb.puppetdb import set_server
from pano.views.views import default_context

__author__ = 'etaklar'


@login_required
def nodes(request):
    context = default_context
    if request.method == 'GET':
        if 'source' in request.GET:
            source = request.GET.get('source')
            set_server(request, source)
    if request.method == 'POST':
        request.session['django_timezone'] = request.POST['timezone']
        return redirect(request.POST['return_url'])

    return render(request, 'pano/nodes.html', context)
