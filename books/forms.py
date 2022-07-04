from django.forms import ModelForm, FileField, FileInput

from .models import Page
from core.widgets import FileValueInput


class PageForm(ModelForm):

    class Meta:
        model = Page
        exclude = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["comments"].widget.attrs["placeholder"] = "Please describe the reason for the upload"
        self.fields["scanned_text"].widget = self.fields["typed_text"].widget = FileValueInput()
        if self.instance.pk:
            disabled_file_field = (
                "typed_text" if self.instance.type == Page.TYPE_SCANNED
                    else "scanned_text"
            )
            for field in ["page_no", "volume_no", disabled_file_field]:
                self.fields[field].disabled = True

    def save(self, **kwargs):
        page = super().save(commit=False)
        if ("typed_text" in self.changed_data or "scanned_text" in self.changed_data):
            page.version_no += 1
            page._change_reason = (
                f"Upload {page.version_no}"
                + ((": " + page.comments) if "comments" in self.changed_data else "")
            )
        else:
            page._change_reason = "No change."
        page.save()
        return page
