from django.contrib.auth.views import LogoutView
from django.urls import path
from .views import (
    ActivationView,
    LoginView,
    RegistrationCompleteView,
    RegistrationView,
    PasswordChangeView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
    UserDetailView,
    UserUpdateView,
)

urlpatterns = [
    path('login/', LoginView.as_view(), name='auth_login'),
    path(
        "logout/",
        LogoutView.as_view(template_name="registration/logout.html"),
        name="auth_logout",
    ),
    path('register/', RegistrationView.as_view(), name='registration_register'),
    path('register/complete/', RegistrationCompleteView.as_view(), name='registration_complete'),
    path('activate/<activation_key>/',
         ActivationView.as_view(),
         name='registration_activate'),
    path('password/reset/', PasswordResetView.as_view(), name='auth_password_reset'),
    path('password/reset/done/', PasswordResetDoneView.as_view(), name='auth_password_reset_done'),
    path('password/reset/confirm/<uidb64>/<token>/',
         PasswordResetConfirmView.as_view(),
         name='auth_password_reset_confirm'),
    path('password/change/', PasswordChangeView.as_view(), name='auth_password_change'),
    path('profile/<uuid:pk>"/detail', UserDetailView.as_view(), name='user_profile'),
    path('profile/<uuid:pk>"/update', UserUpdateView.as_view(), name='edit_user_profile'),

]
