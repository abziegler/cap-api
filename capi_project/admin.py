from django.contrib import admin
from .models import *

class CaseUserAdmin(admin.ModelAdmin):
    readonly_fields = ('date_joined','api_key')
    list_display = ('email', 'last_name', 'first_name', 'api_key')
    def api_key(self, instance):
        return instance.get_api_key()
    api_key.short_description = "API Key"
    fields = ('email', 'first_name', 'last_name', 'case_allowance', 'date_joined', 'api_key', 'is_validated', 'is_researcher', 'is_staff')

class CaseAdmin(admin.ModelAdmin):
    list_display = ('name_abbreviation', 'citation')
    fields = (
        'slug',
        'name',
        'name_abbreviation',
        'firstpage',
        'lastpage',
        'docketnumber',
        'decisiondate',
        'decisiondate_original',
        'jurisdiction',
        'reporter',
        'date_added',
        'court',
    )

class ReporterAdmin(admin.ModelAdmin):
    list_display = ('id', 'name',)
    fields = ('slug', 'name', 'name_abbreviation', 'start_date', 'end_date', 'volumes', 'updated_at', 'jurisdiction')

class CourtAdmin(admin.ModelAdmin):
    list_display = ('id', 'name_abbreviation',)
    fields = ('slug', 'name', 'name_abbreviation', 'jurisdiction')

class JurisdictionAdmin(admin.ModelAdmin):
    list_display = ('id', 'slug', 'name')
    fields = ('slug', 'name', 'name_abbreviation',)

admin.site.register(Case, CaseAdmin)
admin.site.register(CaseUser, CaseUserAdmin)
admin.site.register(Reporter, ReporterAdmin)
admin.site.register(Court, CourtAdmin)
admin.site.register(Jurisdiction, JurisdictionAdmin)
