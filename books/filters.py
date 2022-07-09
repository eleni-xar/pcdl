from crispy_forms.helper import FormHelper
from django.db.models import Exists, OuterRef
from django_filters import CharFilter, ChoiceFilter, FilterSet
from django import forms

from core.filters import PageRangeFilter
from .models import Page


class PageFilterUser(FilterSet):

    page_no = PageRangeFilter(lookup_expr="in")

    class Meta:
        model = Page
        fields = ("page_no", "volume_no",)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.helper = FormHelper(self.form)
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.label_class = "col-form-label-sm"
        self.helper.field_class = "input-group"
        self.helper.wrapper_class = "col-md-3"

    @property
    def qs(self):
        # return super().qs.distinct("volume_no", "page_no")
        parent = super().qs
        typed = parent.filter(type=Page.TYPE_TYPED)
        scanned = parent.filter(type=Page.TYPE_SCANNED)
        duplicates = typed.annotate(is_duplicate=Exists(scanned.filter(page_no=OuterRef("page_no"), volume_no=OuterRef("volume_no"))))
        return scanned | duplicates.filter(is_duplicate=False)


class PageFilterStaff(PageFilterUser):

    type = ChoiceFilter(choices=Page.TYPE_CHOICES)
    comments = CharFilter(
        lookup_expr="icontains", label="Comments contain"
    )

    class Meta(PageFilterUser.Meta):
        fields = ("page_no", "volume_no", "type", "comments")

    @property
    def qs(self):
        return super(FilterSet,self).qs
