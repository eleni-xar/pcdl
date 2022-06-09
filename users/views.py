from django.contrib.auth import views as auth_views, get_user_model
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from registration.backends.default import views as reg_views
from registration import signals

from settings import settings
from .forms import (
	UserCreationForm,
	PasswordResetForm,
	SetPasswordForm,
	UserChangeForm,
)


class LoginView(auth_views.LoginView):
    redirect_authenticated_user = True

    def get_success_url(self):
        if self.redirect_authenticated_user and self.request.user.is_authenticated:
            return settings.LOGIN_REDIRECT_URL
        return super().get_success_url()



class RegistrationView(reg_views.RegistrationView):
    form_class = UserCreationForm

    # success_message = 'Welcome. Your sign up was successful. You can now log in to your account.'

    def get_success_url(self, user):
        return (
            reverse('registration_complete')
            if user.email
            else reverse('auth_login')
        )

    def register(self, form):
        """
        If the user provides an email, register a new
        user account, which will initially be inactive.
        Along with the new ``User`` object, a new
        ``registration.models.RegistrationProfile`` will be created,
        tied to that ``User``, containing the activation key which
        will be used for this account.
        An email will be sent to the supplied email address; this
        email should contain an activation link. The email will be
        rendered using two templates. See the documentation for
        ``RegistrationProfile.send_activation_email()`` for
        information about these templates and the contexts provided to
        them.
        After the ``User`` and ``RegistrationProfile`` are created and
        the activation email is sent, the signal
        ``registration.signals.user_registered`` will be sent, with
        the new ``User`` as the keyword argument ``user`` and the
        class of this backend as the sender.
        If the user, does not provide an email, then they are registered
        as active and redirected to the login page.
        """
        site = get_current_site(self.request)

        if hasattr(form, 'save'):
            new_user_instance = form.save(commit=False)
        else:
            new_user_instance = (get_user_model().objects
                                 .create_user(**form.cleaned_data))

        if new_user_instance.email:
            new_user = self.registration_profile.objects.create_inactive_user(
                new_user=new_user_instance,
                site=site,
                send_email=self.SEND_ACTIVATION_EMAIL,
                request=self.request,
            )
            signals.user_registered.send(sender=self.__class__,
                                         user=new_user,
                                         request=self.request)
        else:
            new_user = new_user_instance
            new_user.is_active = True
            new_user.save()

        return new_user


class PasswordResetView(auth_views.PasswordResetView):

    form_class = PasswordResetForm
    success_url = reverse_lazy('auth_password_reset_done')

    def form_valid(self, form):
        opts = {
            "use_https": self.request.is_secure(),
            "token_generator": self.token_generator,
            "from_email": self.from_email,
            "email_template_name": self.email_template_name,
            "subject_template_name": self.subject_template_name,
            "request": self.request,
            "html_email_template_name": self.html_email_template_name,
            "extra_email_context": self.extra_email_context,
            "domain_override": "127.0.0.1:8000" if settings.DEBUG else None,
        }
        form.save(**opts)
        return super(FormView, self).form_valid(form)


class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):

    form_class = SetPasswordForm

    def get_success_url(self):
        return (
            reverse('home')
            if self.request.user.is_authenticated
            else reverse('auth_login')
        )

    def form_valid(self, form):
        if self.validlink:
            messages.success(
                self.request,
                "Your password was reset successfully. You can now log in."
            )
        return super().form_valid(form)


class PasswordChangeView(auth_views.PasswordChangeView):

    form_class = PasswordChangeForm
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        messages.success(self.request, "Password successfully changed!")
        return super().form_valid(form)

