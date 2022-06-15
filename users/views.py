from django.contrib.auth import views as auth_views, get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.html import mark_safe
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import DetailView, FormView, TemplateView, UpdateView
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

class RegistrationCompleteView(TemplateView):

    template_name = "registration/registration_complete.html"

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return HttpResponseRedirect(reverse('home'))
        return super().get(self, request, *args, **kwargs)

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


class PasswordResetView(auth_views.PasswordResetView):

    form_class = PasswordResetForm
    success_url = reverse_lazy('auth_password_reset_done')

    @method_decorator(csrf_protect)
    def dispatch(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            messages.warning(
                self.request,
                mark_safe(
                """
                You are already logged in. If you wish you can <a href='{}'>change your password.</a>
                """.format(reverse('auth_password_change')))
            )
            return HttpResponseRedirect(reverse('home'))
        return super().dispatch(*args, **kwargs)

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

class PasswordResetDoneView(auth_views.PasswordResetDoneView):

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return HttpResponseRedirect(reverse('home'))
        return super().get(self, request, *args, **kwargs)


class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):

    form_class = SetPasswordForm

    def get_success_url(self):
        return reverse('auth_login')

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


class UserDetailView(LoginRequiredMixin, ProfileMixin, DetailView):

    model = get_user_model()

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        context["form"] = UserProfileForm(
            instance=context["object"],
            disabled=True,
        )
        return context


class UserUpdateView(LoginRequiredMixin, ProfileMixin, SuccessMessageMixin, UpdateView):

    form_class = UserProfileForm
    success_message = 'Your profile has been updated.'

    def get_success_url(self):
        return reverse("user_profile", args=[self.object.username])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["disabled"] = False
        return kwargs
