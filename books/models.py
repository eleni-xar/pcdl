from pathlib import Path
import os

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models, IntegrityError
from django.dispatch import receiver
from django.urls import reverse
from django.utils.html import mark_safe
from simple_history.models import HistoricalRecords

from core.validators import FileValidator


def media_directory_path(instance, filename):
    """
    file will be uploaded to MEDIA_ROOT/volume_<volume_no>/page_<page_no>/
    volume_<volume_no>_page_<page_no>text.<extension>
    """
    volume = instance.volume_no
    page = instance.page_no

    media_path = "volume_{}/page_{}/volume_{}_page_{}_{}{}".format(
        volume,
        page,
        volume,
        page,
        "typed" if instance.type == instance.TYPE_TYPED else "scanned",
        Path(filename).suffix,
    )
    root_path = settings.MEDIA_ROOT + media_path
    if os.path.isfile(root_path):
        os.remove(root_path)
    return media_path


class Page(models.Model):

    TYPE_TYPED = "Typed"
    TYPE_SCANNED = "Scanned"
    TYPE_CHOICES = (
        (TYPE_TYPED, "Typed"),
        (TYPE_SCANNED, "Scanned"),
    )
    page_no = models.IntegerField(
        help_text="The number of the page.",
        verbose_name="page number",
    )
    volume_no = models.PositiveIntegerField(
        help_text="The number of the volume in the series.",
        verbose_name="volume number",
        validators=[
            MinValueValidator(
                1,
                "The volume number must be greater or equal to 1."
            ),
            MaxValueValidator(
                21,
                "The volume number must be less or equal to 21."
            )
        ]
    )
    type = models.CharField(
        max_length=7,
        choices=TYPE_CHOICES,
        blank=True,
    )
    version_no = models.PositiveIntegerField(
        help_text="The version of the uploaded document.",
        verbose_name="version number",
        default=0
    )
    scanned_text = models.FileField(
        help_text="Scanned version of the page.",
        upload_to=media_directory_path,
        blank=True,
        validators=[
            FileValidator(
                max_size=10240000,
                content_types=(
                    "application/pdf",
                )
            )
        ]
    )
    typed_text = models.FileField(
        help_text="Typed version of the page.",
        upload_to=media_directory_path,
        blank=True,
        validators=[
            FileValidator(
                max_size=1024000,
                content_types=(
                    "application/pdf",
                )
            )
        ]
    )
    comments = models.TextField(blank=True)
    history = HistoricalRecords()


    class Meta:
        ordering = ["volume_no", "page_no", "type"]
        constraints = [
            models.UniqueConstraint(
                fields=['volume_no', 'page_no', 'type'],
                name="%(app_label)s_%(class)s_volume_page_type_version_unique"
            ),
            models.CheckConstraint(
                check=models.Q(scanned_text='') | models.Q(typed_text=''),
                name="%(app_label)s_%(class)s_scanned_or_typed_text_null",
            ),
            models.CheckConstraint(
                check=~models.Q(scanned_text="") | ~models.Q(typed_text=''),
                name="%(app_label)s_%(class)s_scanned_or_typed_text_set",
            ),
        ]

    def __str__(self):
        return (
            "Page " + str(self.page_no)
            + " of Volume " + str(self.volume_no)
        )


    def clean(self):
        if not self.scanned_text and not self.typed_text:
            raise ValidationError(
                "Either scanned or typed text must be uploaded."
            )
        if self.scanned_text and self.typed_text:
            raise ValidationError(
                "Scanned and typed text cannot be uploaded together."
            )
        if not self.type:
            self.type = self.TYPE_TYPED if self.typed_text else self.TYPE_SCANNED

        if self.version_no == 0:
            page = Page.objects.filter(
                page_no=self.page_no,
                volume_no=self.volume_no,
                type=self.type,
            ).first()
            if page:
                raise ValidationError(
                    mark_safe(
                        """
                        A {} version of the page {} of volume {} already exists.
                        Please edit <a href='{}'>that page</a> instead of creating a new one.
                        """.format(
                            self.type.lower(),
                            self.page_no,
                            self.volume_no,
                            reverse('admin:books_page_change', args=[str(page.id)])
                        )
                    )
                )
        return super().clean()

    def get_absolute_url(self):
        return reverse("page_detail", args=[str(self.volume_no), str(self.page_no), self.type])


    def find_next_page(self, is_staff=False):
        """
        skip typed text for regular users if a scanned version exists
        """
        if is_staff and self.type == self.TYPE_SCANNED:
            same_page = Page.objects.filter(volume_no=self.volume_no, page_no=self.page_no, type=self.TYPE_TYPED).first()
            if same_page:
                return same_page
        next_page_same_volume = Page.objects.filter(volume_no=self.volume_no, page_no__gt=self.page_no).first()
        next_page_other_volume =  Page.objects.filter(volume_no__gt=self.volume_no).first()
        return (
            next_page_same_volume if next_page_same_volume
            else next_page_other_volume if next_page_other_volume
            else None
        )

    def find_previous_page(self, is_staff=False):
        """
        skip typed text for regular users if a scanned version exists
        """
        if is_staff and self.type == self.TYPE_TYPED:
            same_page = Page.objects.filter(volume_no=self.volume_no, page_no=self.page_no, type=self.TYPE_SCANNED).first()
            if same_page:
                return same_page
        previous_page_same_volume = Page.objects.filter(volume_no=self.volume_no, page_no__lt=self.page_no)
        previous_page_other_volume =  Page.objects.filter(volume_no__lt=self.volume_no)
        if is_staff:
            return (
                previous_page_same_volume.last() if previous_page_same_volume
                else previous_page_other_volume.last() if previous_page_other_volume
                else None
            )
        else:
            return (
                previous_page_same_volume.order_by("volume_no", "page_no", "-type").last() if previous_page_same_volume
                else previous_page_other_volume.order_by("volume_no", "page_no", "-type").last() if previous_page_other_volume
                else None
            )


@receiver(models.signals.pre_delete, sender=Page)
def my_handler(sender, **kwargs):
    instance = kwargs['instance']
    path = (
        instance.typed_text.name if instance.type == instance.TYPE_TYPED
            else instance.scanned_text.name
    )
    dir = settings.MEDIA_ROOT + os.path.split(path)[0]
    if os.path.isdir(dir):
        for file in os.listdir(dir):
            os.remove(os.path.join(dir, file))
