from django.contrib.auth import authenticate, login
from django.shortcuts import redirect, render
import pytz

__author__ = 'etaklar'


def splash(request):
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
                    context = {'timezones': pytz.common_timezones,
                               'login_error': "Account is disabled.",
                               'nexturl': next_url}
                    return render(request, 'pano/splash.html', context)
            else:
                # Return an 'invalid login' error message.
                context = {'timezones': pytz.common_timezones,
                           'login_error': "Invalid credentials",
                           'nexturl': next_url}
                return render(request, 'pano/splash.html', context)
        return redirect('dashboard')
    else:
        user = request.user.username
        context = {'timezones': pytz.common_timezones,
                   'username': user}
        return render(request, 'pano/splash.html', context)
