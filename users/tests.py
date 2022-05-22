from django.contrib.auth import get_user_model
from django.test import TestCase
# from django.urls import reverse, resolve

# from .forms import UserCreationForm
# from .views import SignupView

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
