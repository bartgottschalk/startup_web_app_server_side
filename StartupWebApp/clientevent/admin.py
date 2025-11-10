from django.contrib import admin
from clientevent.models import Pageview, AJAXError, Buttonclick, Linkevent, Configuration
from import_export import resources
from import_export.admin import ImportExportModelAdmin


class PageviewResource(resources.ModelResource):
    class Meta:
        model = Pageview


class PageviewAdmin(ImportExportModelAdmin):
    resource_class = PageviewResource
    list_display = ('user', 'anonymous_id', 'url', 'page_width', 'remote_addr', 'http_user_agent', 'created_date_time')
    list_filter = ('user', 'anonymous_id', 'remote_addr')


class AJAXErrorResource(resources.ModelResource):
    class Meta:
        model = AJAXError


class AJAXErrorAdmin(ImportExportModelAdmin):
    resource_class = AJAXErrorResource
    list_display = ('user', 'anonymous_id', 'url', 'error_id', 'created_date_time')
    list_filter = ('user', 'anonymous_id', 'url', 'error_id')


class ButtonclickResource(resources.ModelResource):
    class Meta:
        model = Buttonclick


class ButtonclickAdmin(ImportExportModelAdmin):
    resource_class = ButtonclickResource
    list_display = ('user', 'anonymous_id', 'url', 'button_id', 'created_date_time')
    list_filter = ('user', 'anonymous_id', 'url', 'button_id')


class LinkeventResource(resources.ModelResource):
    class Meta:
        model = Linkevent


class LinkeventAdmin(ImportExportModelAdmin):
    resource_class = LinkeventResource
    list_display = ('user', 'prospect', 'anonymous_id', 'email', 'ad', 'url', 'created_date_time')
    list_filter = ('user', 'prospect', 'anonymous_id', 'email', 'ad', 'url')


# Register your models here.
admin.site.register(Pageview, PageviewAdmin)
admin.site.register(AJAXError, AJAXErrorAdmin)
admin.site.register(Buttonclick, ButtonclickAdmin)
admin.site.register(Linkevent, LinkeventAdmin)
admin.site.register(Configuration)
