from django.test import SimpleTestCase
from django.urls import reverse, resolve

from .views import HomeView

class HomePageTests(SimpleTestCase):

    def setUp(self):
        self.response = self.client.get(reverse('home'))

    def test_homepage_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_homepage_template(self):
        self.assertTemplateUsed(self.response, 'home.html')

    def test_homepage_content(self):
        self.assertContains(self.response, 'Welcome')
        self.assertNotContains(self.response, 'Hi there')

    def test_homepage_resolve(self):
        view = resolve('/')
        self.assertEqual(
            view.func.__name__,
            HomeView.as_view().__name__
        )
