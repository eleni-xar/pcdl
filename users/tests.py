from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse, resolve

from .forms import UserCreationForm
from .views import RegistrationView

User = get_user_model()

class UserTests(TestCase):

    def test_create_user(self):

        # Successfully create user
        user = User.objects.create_user(
            username="user",
            email="user@test.org",
            password="userpass"
        )

        self.assertEqual(user.username, "user")
        self.assertEqual(user.email, "user@test.org")
        self.assertTrue(user.check_password("userpass"))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

        # Fail to create user with existing username
        try:
            with transaction.atomic():
                user2 = User.objects.create_user(
                    username="user",
                    email="user2@test.org",
                    password="userpass"
                )
        except:
            pass

        self.assertFalse(User.objects.filter(email="user2@test.org").exists())

        # Allow user with same email
        user2 = User.objects.create_user(
            username="user2",
            email="user@test.org",
            password="userpass"
        )

        self.assertEqual(user.email, user2.email)


    def test_create_superuser(self):

        # Succesfully create superuser.
        user = User.objects.create_superuser(
            username="su",
            email="su@test.org",
            password="sutesting"
        )

        self.assertEqual(user.username, "su")
        self.assertEqual(user.email, "su@test.org")
        self.assertTrue(user.check_password("sutesting"))
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

        ## Fail to create superuser with existing username.
        try:
            with transaction.atomic():
                user2 = User.objects.create_superuser(
                    username="su",
                    email="su2@test.org",
                    password="sutesting"
                )
        except:
            pass

        self.assertFalse(User.objects.filter(email="su2@test.org").exists())
        self.assertEqual(User.objects.all().count(), 1)


class LoginViewTests(TestCase):

    def setUp(self):
        self.url = reverse('auth_login') + '?next=/wrong/'

    def test_redirect_logged_in_user(self):
        """
        next should work only with users who are not already logged in.
        In this test the value of next is a non existing page so 404 is returned
        the first time. Whe the user tries to log in again, they are redirected
        to the home page.
        """
        User.objects.create_user(
            username='testuser',
            password='somepass'
        )
        response1 = self.client.post(
            self.url,
            {
                'username':'testuser',
                'password':'somepass',
            },
            follow=True
        )
        self.assertEqual(response1.status_code, 404)

        response2 = self.client.post(
            self.url,
            {
                'username':'testuser',
                'password':'somepass',
            },
            follow=True
        )
        self.assertEqual(response2.redirect_chain, [('/', 302)])
        self.assertEqual(response2.status_code, 200)
        self.assertContains(response2, 'Welcome')


class SignupViewTests(TestCase):

    username = 'testuser'
    email = 'test@test.org'

    def setUp(self):
        self.url = reverse('register')
        self.response = self.client.get(self.url)

    def test_register_template(self):
        self.assertEqual(self.response.status_code, 200)
        self.assertTemplateUsed(self.response, 'registration/registration_form.html')
        self.assertContains(self.response, 'open an account')
        self.assertNotContains(self.response, 'Log Out')

    def test_register_view(self):
        view = resolve('/accounts/register/')
        self.assertEqual(
            view.func.__name__,
            RegistrationView.as_view().__name__
        )

    def test_register_form(self):
        form = self.response.context.get('form')
        self.assertIsInstance(form, UserCreationForm)
        self.assertContains(self.response, 'csrfmiddlewaretoken')

    def test_register_form_no_email(self):
        # possible to sign up without email
        response = self.client.post(
            self.url,
            {
                'username':self.username,
                'password1':'somepass',
                'password2':'somepass'
            },
            follow=True
        )
        self.assertEqual(response.redirect_chain, [('/accounts/login/', 302)])
        self.assertEqual(User.objects.all().count(), 1)
        self.assertTrue(User.objects.filter(username=self.username).exists())

    def test_register_form_with_email(self):
        response = self.client.post(
            self.url,
            {
                'username':self.username,
                'email':self.email,
                'password1':'somepass',
                'password2':'somepass'
            },
            follow=True
        )
        self.assertEqual(response.redirect_chain, [('/accounts/register/complete/', 302)])
        self.assertEqual(User.objects.all().count(), 1)
        user = User.objects.all()[0]
        self.assertEqual(user.username, self.username)
        self.assertEqual(user.email, self.email)

    def test_register_form_same_username(self):
        response1 = self.client.post(
            self.url,
            {
                'username':self.username,
                'password1':'somepass',
                'password2':'somepass'
            },
        )
        response2 = self.client.post(
            self.url,
            {
                'username':self.username,
                'password1':'somepass',
                'password2':'somepass'
            },
        )
        self.assertEqual(User.objects.all().count(), 1)
        self.assertContains(response2, 'already exists')
