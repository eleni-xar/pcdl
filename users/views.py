from django.contrib.auth import views as auth_views, get_user_model, REDIRECT_FIELD_NAME
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.sites.shortcuts import get_current_site
from django.dispatch import receiver
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import DetailView, UpdateView, FormView
from django.views.generic.detail import SingleObjectMixin
from registration.backends.default import views as reg_views
from registration.models import RegistrationProfile
from registration import signals

from settings import settings
from .forms import (
    PasswordChangeForm,
    PasswordResetForm,
    SetPasswordForm,
    UserChangeForm,
    UserCreationForm,
    UserProfileForm,
)


class LoginView(auth_views.LoginView):
    redirect_authenticated_user = True


    @method_decorator(sensitive_post_parameters())
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        if self.redirect_authenticated_user and self.request.user.is_authenticated:
            redirect_to = settings.LOGIN_REDIRECT_URL
            if redirect_to == self.request.path:
                raise ValueError(
                    "Redirection loop for authenticated user detected. Check that "
                    "your LOGIN_REDIRECT_URL doesn't point to a login page."
                )
            return HttpResponseRedirect(redirect_to)
        return super().dispatch(request, *args, **kwargs)



class RegistrationView(reg_views.RegistrationView):
    form_class = UserCreationForm

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


class ActivationView(reg_views.ActivationView):

    def get_success_url(self, user):
        messages.success(
            self.request,
            "Your account has been activated."
        )
        if self.request.user.is_authenticated:
            return reverse('home')
        else:
            return reverse('auth_login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        activation_key = context['activation_key']
        context["profile"] = RegistrationProfile.objects.filter(activation_key=activation_key).first()
        return context

    def get(self, request, *args, **kwargs):
        activation_key = self.get_context_data(**kwargs)["activation_key"]
        profile = RegistrationProfile.objects.filter(activation_key=activation_key).first()
        if profile and profile.activated:
            return self.render_to_response(self.get_context_data(**kwargs))
        return super().get(request, *args, **kwargs)


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


class ProfileMixin(SingleObjectMixin):

    slug_field = "username"
    slug_url_kwarg = "username"
    template_name = 'registration/user_form.html'

    def get_object(self):
        return self.request.user



class UserDetailView(ProfileMixin, DetailView):

    model = get_user_model()

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        context["form"] = UserProfileForm(
            instance=context["object"],
            disabled=True,
        )
        return context


class UserUpdateView(ProfileMixin, SuccessMessageMixin, UpdateView):

    form_class = UserProfileForm
    success_message = 'Your profile has been updated.'

    def get_success_url(self):
        return reverse("user_profile", args=[self.object.username])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["disabled"] = False
        return kwargs
