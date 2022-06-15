from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import Client, TestCase, TransactionTestCase
from django.urls import reverse, resolve
from registration.models import RegistrationProfile

from .forms import UserCreationForm
from settings import settings

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
        url = reverse('registration_register')
        self.response = self.client.get(url)

    def test_register_template(self):
        self.assertEqual(self.response.status_code, 200)
        self.assertTemplateUsed(self.response, 'registration/registration_form.html')
        self.assertContains(self.response, 'open an account')
        self.assertNotContains(self.response, 'Log Out')

    def test_register_form(self):
        form = self.response.context.get('form')
        self.assertIsInstance(form, UserCreationForm)
        self.assertContains(self.response, 'Already a user?')


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

class RegistrationCompleteViewTests(TestCase):

    def test_registration_complete_template(self):
        """
        Uses correct template if user is not logged in
        """
        url = reverse('registration_complete')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/registration_complete.html')
        self.assertContains(response, 'Thank you for signing up')

        """
        Redirects to home if user is logged in.
        """
        user = User.objects.create_user(username=username)
        self.client.force_login(user)
        response = self.client.get(url)
        self.assertRedirects(response, reverse('home'))


class ActivationViewTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        """
        Register a user. Used for both tests.
        """
        myclient = Client()
        myclient.post(
            reverse("registration_register"),
            data={
                'username':username,
                'email':email,
                'password1':password,
                'password2':password
            },
        )

    def activation_response(self, activation_key):
        return self.client.get(
            reverse(
                'registration_activate',
                args=[],
                kwargs={'activation_key': activation_key}
                ),
            follow=True
            )

    def test_activation(self):
        """
        First time the activation key is used, the profile is activated,
        the user becomes active, and is redirected to login.
        """

        user = User.objects.filter(username=username).first()
        profile = RegistrationProfile.objects.filter(user=user).first()

        response = self.activation_response(profile.activation_key)

        activated_user = User.objects.filter(username=username).first()
        self.assertTrue(activated_user.is_active)
        self.assertTrue(RegistrationProfile.objects.filter(user=activated_user).first().activated)

        self.assertRedirects(response, reverse('auth_login'))
        self.assertContains(response, 'Your account has been activated')

        """
        A logged in user is redirected to home page.
        """
        self.client.force_login(user)

        response = self.activation_response(profile.activation_key)
        self.assertRedirects(response, reverse('home'))
        self.assertContains(response, "Your account has been activated")

    def test_failed_activation(self):
        """
        After the key is expired, user is redirected to activate.html,
        and is prompted to try signing up again.
        """

        user = User.objects.filter(username=username).first()
        user.date_joined -= timedelta(
            days=settings.ACCOUNT_ACTIVATION_DAYS)
        user.save()
        profile = RegistrationProfile.objects.filter(user=user).first()

        response = self.activation_response(profile.activation_key)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/activate.html')
        self.assertContains(response, "try again")
