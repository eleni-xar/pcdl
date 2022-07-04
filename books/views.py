from django.contrib.auth.mixins import LoginRequiredMixin
from django_filters.views import FilterView
from django.http import Http404
from django_tables2 import SingleTableMixin
from django.views.generic.detail import DetailView

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


class PageDetailView(LoginRequiredMixin, DetailView):
    model = Page
    context_object_name = "page"
    template_name = "books/page_detail.html"
    page_slug_field = "page_no"
    page_slug_url_kwarg = "page"
    volume_slug_field = "volume_no"
    volume_slug_url_kwarg = "volume"
    type_slug_field = "type"
    type_slug_url_kwarg = "type"

    def get_object(self, queryset=None):
        page_slug = self.kwargs.get(self.page_slug_url_kwarg)
        volume_slug = self.kwargs.get(self.volume_slug_url_kwarg)
        type_slug = self.kwargs.get(self.type_slug_url_kwarg)
        queryset = Page.objects.filter(
            **{
                self.page_slug_field: page_slug,
                self.volume_slug_field: volume_slug
            }
        )
        if not self.request.user.is_staff:
            try:
                obj = queryset.filter(type=Page.TYPE_SCANNED).get()
            except queryset.model.DoesNotExist:
                try:
                    obj = queryset.filter(type=Page.TYPE_TYPED).get()
                except queryset.model.DoesNotExist:
                    raise Http404(
                        "No %(verbose_name)s found matching the query"
                        % {"verbose_name": queryset.model._meta.verbose_name}
                    )
        else:
            try:
                obj = queryset.filter(type=type_slug).get()
            except queryset.model.DoesNotExist:
                raise Http404(
                    "No %(verbose_name)s found matching the query"
                    % {"verbose_name": queryset.model._meta.verbose_name}
                )
        return obj


    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        page = context["page"]
        context["next_page"] = (
            page.find_next_page(is_staff=True) if self.request.user.is_staff
                else page.find_next_page()
        )
        context["previous_page"] = (
            page.find_previous_page(is_staff=True) if self.request.user.is_staff
                else page.find_previous_page()
        )
        return context
