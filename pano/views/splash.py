__author__ = 'etaklar'
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect, render
from pano.puppetdb.puppetdb import set_server
from pano.settings import AVAILABLE_SOURCES
import pytz


def splash(request):
    context = {'timezones': pytz.common_timezones,
               'SOURCES': AVAILABLE_SOURCES}
    if request.method == 'GET':
        if 'source' in request.GET:
            source = request.GET.get('source')
            set_server(request, source)
    if request.method == 'POST':
        if 'timezone' in request.POST:
            request.session['django_timezone'] = request.POST['timezone']
            return redirect(request.POST['url'])
        elif 'username' in request.POST and 'password' in request.POST:
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(username=username, password=password)
            next_url = False
            if 'nexturl' in request.POST:
                next_url = request.POST['nexturl']
            if user is not None:
                if user.is_active:
                    login(request, user)
                    if next_url:
                        return redirect(next_url)
                    else:
                        return redirect('dashboard')
                else:
                    context['login_error'] = "Account is disabled."
                    context['nexturl'] = next_url
                    return render(request, 'pano/splash.html', context)
            else:
                # Return an 'invalid login' error message.
                context['login_error'] = "Invalid credentials"
                context['nexturl'] = next_url
                return render(request, 'pano/splash.html', context)
        return redirect('dashboard')

    user = request.user.username
    context['username'] = user
    return render(request, 'pano/splash.html', context)
