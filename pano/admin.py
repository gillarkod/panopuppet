from django.contrib import admin
from .models import LdapGroupPermissions


class LdapGroupsAdmin(admin.ModelAdmin):
    search_fields = ['ldap_group_name']


admin.site.register(LdapGroupPermissions, LdapGroupsAdmin)
