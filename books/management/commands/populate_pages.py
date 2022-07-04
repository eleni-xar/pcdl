from random import sample
from itertools import product
import os
from PIL import Image
import tempfile

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from ...models import Page


class Command(BaseCommand):
    def handle(self, *args, **options):
        """
        Populate the basic database with pages.
        """
        if not settings.DEBUG:
            raise AssertionError("Do not run this on Production!")

        sample_space = set(product(set(range(1,501)), set(range(2,22))))

        page_typed_sample = sample(sample_space,250)
        page_scanned_sample = sample(sample_space, 250)

        with open("pcdl_docs/test_pdf.pdf", 'rb') as f:
            wrapped_file = File(f)
            # 25 pages with both scanned and typed text
            for i in range(0, 25):
                Page.objects.create(
                    page_no=i+1,
                    volume_no=1,
                    type=Page.TYPE_TYPED,
                    typed_text=wrapped_file
                )
                Page.objects.create(
                    page_no=i+1,
                    volume_no=1,
                    type=Page.TYPE_SCANNED,
                    scanned_text=wrapped_file
                )
            # 250 random pages with typed text
            for page_no, volume_no in page_typed_sample:
                Page.objects.create(
                    page_no=page_no,
                    volume_no=volume_no,
                    type=Page.TYPE_TYPED,
                    typed_text=wrapped_file
                )
            # 250 random pages with scanned text
            for page_no, volume_no in page_scanned_sample:
                Page.objects.create(
                    page_no=page_no,
                    volume_no=volume_no,
                    type=Page.TYPE_SCANNED,
                    scanned_text=wrapped_file
                )
