from django.forms import Field
from django_filters import Filter
from django_filters.widgets import CSVWidget
from django_filters.constants import EMPTY_VALUES

from core.validators import validate_page_filter


class PageRangeField(Field):

    widget = CSVWidget(attrs={"class":"form-control"})

    default_validators = [validate_page_filter]


class PageRangeFilter(Filter):

    field_class = PageRangeField

    def filter(self, qs, value):
        if value in EMPTY_VALUES:
            return qs
        value_list = []
        for v in value:
            v = v.strip()
            if '-' not in v:
                value_list.append(int(v))
            else:
                start = int(v.split('-')[0])
                end = int(v.split('-')[1]) + 1
                value_list.extend(range(start, end))

        qs = super().filter(qs, value_list)
        return qs
