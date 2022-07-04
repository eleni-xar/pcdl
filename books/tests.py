import os
from PIL import Image
import tempfile
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings, TestCase
from django.urls import reverse

from core.widgets import FileValueInput
from .models import Page
from .forms import PageForm

file_mock_text = mock.MagicMock(spec=File, name='FileMockText')
file_mock_text.name = 'test1.txt'

dir = tempfile.gettempdir()
image = Image.new("RGB", (1, 1), (255, 0, 0))
image_path = os.path.join(dir, "image.png")
image.save(image_path, 'png')

class PageErrorTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_superuser(username="test")
        cls.url = reverse('admin:books_page_add')

    def setUp(self):
        self.client.force_login(self.user)
        self.response = self.client.get(self.url)

    def test_volume_values(self):
        """
        Error if volume number is not between 1 and 21.
        """
        with open("pcdl_docs/test_pdf.pdf", 'rb') as f:
            wrapped_file = File(f)
            # more than 21
            response = self.client.post(
                self.url,
                {
                    "page_no":3,
                    "volume_no":22,
                    "typed_text":wrapped_file
                },
            )
            # less than 1
            self.assertContains(response, "less or equal to 21")
            response = self.client.post(
                self.url,
                {
                    "page_no":3,
                    "volume_no":0,
                    "typed_text":wrapped_file
                }
            )
            self.assertContains(response, "greater or equal to 1")

    def test_file_validation(self):
        """
        Error when trying to upload files of wrong content type
        """
        # upload a png as typed text
        photo = SimpleUploadedFile(name='image.png', content=open(image_path, 'rb').read(), content_type='image/png')
        response = self.client.post(
            self.url,
            {
                "page_no":3,
                "volume_no":3,
                "typed_text":photo
            },follow=True
        )
        self.assertContains(response, "Files of type image/png are not supported.")

        # upload a txt as scanned text
        response = self.client.post(
            self.url,
            {
                "page_no":3,
                "volume_no":3,
                "scanned_text":file_mock_text
            }
        )
        self.assertContains(response, "Files of type text/plain are not supported.")

    def test_file_upload_fails(self):
        """
        Error when wrong number of files is uploaded
        """
        # no files
        response = self.client.post(
            self.url,
            {
                "page_no":3,
                "volume_no":3,
            }
        )
        self.assertContains(response, "Either scanned or typed text must be uploaded")

        # 2 files
        with open("pcdl_docs/test_pdf.pdf", 'rb') as f1:
            with open("pcdl_docs/test_pdf.pdf", 'rb') as f2:
                wrapped_file_1 = File(f1)
                wrapped_file_2 = File(f2)

                response = self.client.post(
                    self.url,
                    {
                        "page_no":3,
                        "volume_no":3,
                        "scanned_text":wrapped_file_1,
                        "typed_text":wrapped_file_2
                    }
                )
        # print(response.rendered_content)
        self.assertContains(response, "Scanned and typed text cannot be uploaded together.")


class PageTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_superuser(username="test")
        cls.add_url = reverse('admin:books_page_add')

    @override_settings(MEDIA_ROOT=dir + '/')
    def setUp(self):
        """
        Use admin to create a page
        """
        self.client.force_login(self.user)
        self.get_response = self.client.get(self.add_url)
        with open("pcdl_docs/test_pdf.pdf", 'rb') as f:
            wrapped_file = File(f)
            self.post_response = self.client.post(
                self.add_url,
                {
                    "page_no":3,
                    "volume_no":3,
                    "typed_text":wrapped_file,
                },
                follow=True
            )
        self.page = Page.objects.first()
        self.change_url = reverse('admin:books_page_change', args=[self.page.pk])


    def test_page_create(self):
        """
        The page is created and stored with the correct name.
        It has the correct type and version number.
        """

        self.assertContains(self.post_response, 'was added successfully.')
        self.assertEqual(Page.objects.count(), 1)
        self.assertTrue(os.path.isfile(os.path.join(dir, "volume_3", "page_3", "volume_3_page_3_typed.pdf" )))
        self.assertEqual(self.page.volume_no, 3)
        self.assertEqual(self.page.page_no, 3)
        self.assertEqual(self.page.type, Page.TYPE_TYPED)
        self.assertEqual(self.page.version_no, 1)

    def test_not_create_same_page_twice(self):
        """
        Fail to create the same page again.
        """
        response = self.client.get(self.add_url)
        with open("pcdl_docs/test_pdf.pdf", 'rb') as f:
            wrapped_file = File(f)
            response = self.client.post(
                self.add_url,
                {
                    "page_no":3,
                    "volume_no":3,
                    "typed_text":wrapped_file,
                }
            )
        self.assertContains(response, 'A typed version of the page 3 of volume 3 already exists.')
        self.assertEqual(Page.objects.count(), 1)

    @override_settings(MEDIA_ROOT=dir + '/')
    def test_update_page(self):
        """
        Updating the page changes the version, but not the name of the file.
        The version number is increased by 1.
        """

        response = self.client.get(self.change_url)
        with open("pcdl_docs/test_pdf.pdf", 'rb') as f:
            wrapped_file = File(f)
            response = self.client.post(
                self.change_url,
                {
                    "page_no":3,
                    "volume_no":3,
                    "typed_text":wrapped_file,
                },
                follow=True
            )
        self.assertContains(response, 'was changed successfully.')
        # the saved file is the same
        saved_files = (os.listdir(os.path.join(dir, "volume_3", "page_3")))
        self.assertEqual(len(saved_files), 1)
        self.assertTrue(os.path.isfile(os.path.join(dir, "volume_3", "page_3", "volume_3_page_3_typed.pdf" )))
        # The version number has increased
        page = Page.objects.first()
        self.assertEqual(page.version_no, 2)

    @override_settings(MEDIA_ROOT=dir + '/')
    def test_delete_file_after_deleting_page(self):
        """
        The file is deleted once the page is deleted
        """
        self.page.delete()
        self.assertFalse(os.path.isfile(os.path.join(dir, "volume_3", "page_3", "volume_3_page_3_typed.txt" )))
        saved_files = (os.listdir(os.path.join(dir, "volume_3", "page_3")))
        self.assertEqual(len(saved_files), 0)

    def test_admin_form(self):
        """
        The correct form is used and page number, volume number and alternative
        file field are disabled when updating a page.
        """

        form = self.get_response.context.get('adminform').form
        self.assertIsInstance(form, PageForm)
        # when adding page no field is disabled
        for field in form.fields:
            self.assertFalse(form.fields[field].disabled)

        response = self.client.get(self.change_url)
        # FileValueInput is used instead of ClearableFileInput.
        self.assertNotContains(response, "checkbox")
        self.assertIsInstance(form.fields["typed_text"].widget, FileValueInput)

        # page number, volume number and alternative file field are disabled when updating
        form = response.context.get('adminform').form
        self.assertIsInstance(form, PageForm)
        for field in ["page_no", "volume_no", "scanned_text"]:
            self.assertTrue(form.fields[field].disabled)

    @override_settings(MEDIA_ROOT=dir + '/')
    def test_page_history(self):
        """
        History page includes the correct reasons and has a close button.
        Reverting is disabled.
        """

        response = self.client.get(self.change_url)
        with open("pcdl_docs/test_pdf.pdf", 'rb') as f:
            wrapped_file = File(f)
            response = self.client.post(
                self.change_url,
                {
                    "page_no":3,
                    "volume_no":3,
                    "typed_text":wrapped_file,
                },
                follow=True
            )
        response = self.client.get(reverse('admin:books_page_history', args=[self.page.pk]))
        # Change reason
        self.assertContains(response, "Upload 2")
        # Close button
        self.assertContains(
            response,
            "<a href=\"{}\" class=\"closelink\">Close</a>".format(
                self.change_url
            ),
            html=True,
        )
        # This is present only if reverting is enabled
        self.assertNotContains(response, "Choose an entry from the list below")


class PageViewTests(TestCase):

    @classmethod
    @override_settings(MEDIA_ROOT=dir + '/')
    def setUpTestData(cls):
        with open("pcdl_docs/test_pdf.pdf", 'rb') as f:
            wrapped_file = File(f)
            cls.page1 = Page.objects.create(
                page_no=23,
                volume_no=12,
                scanned_text=wrapped_file,
            )
        cls.page1.type = Page.TYPE_SCANNED
        cls.page1.save()
        with open("pcdl_docs/test_pdf.pdf", 'rb') as f:
            wrapped_file = File(f)
            cls.page2 = Page.objects.create(
                page_no=23,
                volume_no=12,
                typed_text=wrapped_file,
            )
        cls.page2.type = Page.TYPE_TYPED
        cls.page2.save()
        with open("pcdl_docs/test_pdf.pdf", 'rb') as f:
            wrapped_file = File(f)
            cls.page3 = Page.objects.create(
                page_no=35,
                volume_no=12,
                scanned_text=wrapped_file,
            )
        cls.page3.type = Page.TYPE_SCANNED
        cls.page3.save()
        with open("pcdl_docs/test_pdf.pdf", 'rb') as f:
            wrapped_file = File(f)
            cls.page4 = Page.objects.create(
                page_no=36,
                volume_no=14,
                scanned_text=wrapped_file,
            )
        cls.page4.type = Page.TYPE_SCANNED
        cls.page4.save()
        cls.superuser = get_user_model().objects.create_superuser(username="su_test")
        cls.user = get_user_model().objects.create_user(username="test")

    def test_page_list_view_superuser(self):
        """
        Superuser can see and filter comments, and types. They see all pages.
        """
        self.client.force_login(self.superuser)
        response = self.client.get(reverse("page_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "books/page_list.html")
        self.assertContains(response, "23")
        self.assertContains(response, "Upload number")
        self.assertContains(response, "Comments contain")
        self.assertContains(response, "Total: 4")


    def test_page_list_view_regular_user(self):
        """
        Regular uuser cannot see and filter comments, and types. They do not see duplicates.
        """
        self.client.force_login(self.user)
        response = self.client.get(reverse("page_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "books/page_list.html")
        self.assertContains(response, "23")
        self.assertNotContains(response, "Upload number")
        self.assertNotContains(response, "Comments contain")
        self.assertContains(response, "Total: 3")

    def test_page_filter(self):
        """
        Returns error when format of input is wrong
        """
        self.client.force_login(self.superuser)
        response = self.client.get(reverse("page_list") + "?page_no=a")
        self.assertContains(response, "Values must be a range or separate page numbers")
        response = self.client.get(reverse("page_list") + "?page_no=22-a")
        self.assertContains(response, "Values must be a range or separate page numbers")
        response = self.client.get(reverse("page_list") + "?page_no=a-24")
        self.assertContains(response, "Values must be a range or separate page numbers")
        response = self.client.get(reverse("page_list") + "?page_no=22-24%2Ca")
        self.assertContains(response, "Values must be a range or separate page numbers")
        response = self.client.get(reverse("page_list") + "?page_no=22;24")
        self.assertContains(response, "Values must be a range or separate page numbers")
        response = self.client.get(reverse("page_list") + "?page_no=22.24")
        self.assertContains(response, "Values must be a range or separate page numbers")
        response = self.client.get(reverse("page_list") + "?page_no=23-35")
        # correct number of results when input is right
        self.assertContains(response, "Total: 3")

