import django_tables2 as tables
from django.utils.html import mark_safe


from .models import Page

class PageTableUser(tables.Table):

    page_no = tables.Column(
        footer=lambda table: mark_safe(
            f"<strong>Total: {len(table.data)}</strong>"
        ),
    )


    class Meta:
        model = Page
        template_name = "django_tables2/bootstrap4.html"
        fields = ("page_no", "volume_no" )
        per_page = 100
        attrs = {
            "class": "table table-sortable table-sm",
            "th": {"class": "text-uppercase"},
        }

    def render_page_no(self, record, value):
        file_url = record.typed_text.url if record.type == "Typed" else record.scanned_text.url
        return mark_safe(
        "<a href='{}'>{}</a>".format(
            file_url,
            value
        )
    )


class PageTableStaff(PageTableUser):

    version_no = tables.Column(verbose_name="Upload number")

    class Meta(PageTableUser.Meta):
        fields = ("page_no", "volume_no", "type", "version_no", "comments")
