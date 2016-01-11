from django.contrib.auth.decorators import login_required

__author__ = 'etaklar'


@login_required
def api(request):
    return False
