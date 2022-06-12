from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, TransactionTestCase
from django.urls import reverse, resolve
from registration.models import RegistrationProfile

from .forms import UserCreationForm
from .views import RegistrationView

User = get_user_model()

username = 'testuser'
email = 'test@test.org'
password = 'somepass'

class UserTests(TestCase):

    def test_create_user(self):

        # Successfully create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
        )

        self.assertEqual(user.username, username)
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

        # Fail to create user with existing username
        try:
            with transaction.atomic():
                user2 = User.objects.create_user(
                    username=username,
                    password=password
                )
        except:
            pass

        self.assertEqual(User.objects.all().count(), 1)

        # Allow user with same email
        user2 = User.objects.create_user(
            username="user2",
            email=email,
            password=password
        )

        self.assertEqual(user.email, user2.email)


    def test_create_superuser(self):

        # Succesfully create superuser.
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )

        self.assertEqual(user.username, username)
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

        ## Fail to create superuser with existing username.
        try:
            with transaction.atomic():
                user2 = User.objects.create_superuser(
                    username=username,
                    password=password
                )
        except:
            pass

        self.assertEqual(User.objects.all().count(), 1)


class LoginViewTests(TestCase):

    def setUp(self):
        self.url = reverse('auth_login') + '?next=/wrong/'

    def test_login_redirect(self):
        """
        next should work only with users who are not already logged in.
        In this test the value of next is a non existing page so 404 is returned
        the first time. When the user tries to log in again, they are redirected
        to the home page.
        """
        User.objects.create_user(
            username=username,
            password=password
        )
        response1 = self.client.post(
            self.url,
            {
                'username':username,
                'password':password,
            },
            follow=True
        )
        self.assertEqual(response1.status_code, 404)

        response2 = self.client.post(
            self.url,
            {
                'username':username,
                'password':password,
            },
            follow=True
        )
        self.assertRedirects(response2, reverse("home"))


class RegistrationViewGetTests(TestCase):

    def setUp(self):
        self.url = reverse('registration_register')
        self.response_get = self.client.get(self.url)

    def test_register_template(self):
        self.assertEqual(self.response_get.status_code, 200)
        self.assertTemplateUsed(self.response_get, 'registration/registration_form.html')
        self.assertContains(self.response_get, 'open an account')
        self.assertNotContains(self.response_get, 'Log Out')

    def test_register_form(self):
        form = self.response_get.context.get('form')
        self.assertIsInstance(form, UserCreationForm)
        self.assertContains(self.response_get, 'csrfmiddlewaretoken')


class RegistrationViewPostTests(TransactionTestCase):

    def setUp(self):
        self.url = reverse('registration_register')
        self.data = {
            'username':username,
            'password1':password,
            'password2':password,
        }


    def test_register_form_no_email(self):
        """
        possible to sign up without email; one active user is created;
        no email is sent; user is redirected to login.
        """
        response = self.client.post(self.url, data=self.data)
        self.assertRedirects(response, reverse('auth_login'))
        self.assertEqual(User.objects.all().count(), 1)
        user = User.objects.all()[0]
        self.assertEqual(user.username, username)
        self.assertTrue(user.check_password(password))
        self.assertTrue(user.is_active)

    def test_register_form_with_email(self):
        """
        sign up with email; user is redirected to registration complete message;
        inactive user i created; an email is sent;
        """
        self.data["email"] = email
        response = self.client.post(self.url, data=self.data)
        self.assertRedirects(response, reverse('registration_complete'))
        self.assertEqual(User.objects.count(), 1)
        user = User.objects.all()[0]
        self.assertEqual(user.username, username)
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))
        self.assertFalse(user.is_active)
        self.assertEqual(RegistrationProfile.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_register_form_same_username(self):
        """
        Fail to sign up user if the provided username is taken.
        """
        response1 = self.client.post(
            self.url,
            data=self.data,
        )
        response2 = self.client.post(
            self.url,
            data=self.data,
        )
        self.assertEqual(User.objects.all().count(), 1)
        self.assertContains(response2, 'already exists')
