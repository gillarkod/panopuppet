from django.conf.urls import patterns, include, url
from django.contrib import admin

urlpatterns = patterns('',
                       # Examples:
                       # url(r'^$', 'puppet.views.home', name='home'),
                       # url(r'^blog/', include('blog.urls')),
                       url(r'^$', include('panopuppet.pano.urls')),
                       url(r'^pano/', include('panopuppet.pano.urls')),
                       url(r'^puppetadmin/', include(admin.site.urls)),
)
