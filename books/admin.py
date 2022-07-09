from django.contrib import admin
from django.core.exceptions import ValidationError
# from simple_history.admin import SimpleHistoryAdmin

from .models import Page
from .forms import PageForm
from core.admin import CustomHistoryAdmin

class PageAdmin(CustomHistoryAdmin):
    list_display = ("page_no", "volume_no", "type", "comments")
    exclude = ("version_no",)
    history_list_display = ["type"]
    search_fields = ["page_no"]
    list_filter = ("type", "volume_no")
    search_help_text = "Give a page number"
    readonly_fields = ("type",)
    form = PageForm

    def has_module_permission(self, request, *args, **kwargs):
        return (request.user.is_superuser or request.user.is_staff)

    def has_view_permission(self, request, *args, **kwargs):
        return (request.user.is_superuser or request.user.is_staff)

    def has_add_permission(self, request, *args, **kwargs):
        return (request.user.is_superuser or request.user.is_staff)

    def has_change_permission(self, request, *args, **kwargs):
        return (request.user.is_superuser or request.user.is_staff)

    def has_delete_permission(self, request, *args, **kwargs):
        return (request.user.is_superuser or request.user.is_staff)

admin.site.register(Page, PageAdmin)
