from django.contrib.auth.mixins import LoginRequiredMixin
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin

from .filters import PageFilterStaff, PageFilterUser
from .models import Page
from .tables import PageTableStaff, PageTableUser


class PageListView(LoginRequiredMixin, SingleTableMixin, FilterView):
    model = Page
    context_object_name = "page_list"
    template_name = "books/page_list.html"

    def get_table_class(self, **kwargs):
        return PageTableStaff if self.request.user.is_staff else PageTableUser

    def get_filterset_class(self, **kwargs):
        return PageFilterStaff if self.request.user.is_staff else PageFilterUser