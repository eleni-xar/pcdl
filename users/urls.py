from django.urls import path
from .views import (
    ActivationView,
    LoginView,
    RegistrationView,
    PasswordChangeView,
    PasswordResetConfirmView,
    PasswordResetView,
)

urlpatterns = [
    path('login/', LoginView.as_view(), name='auth_login'),
    path('register/', RegistrationView.as_view(), name='register'),
     path('activate/<activation_key>/',
         ActivationView.as_view(),
         name='registration_activate'),
    path('password/reset/', PasswordResetView.as_view(), name='auth_password_reset'),
    path('password/reset/confirm/<uidb64>/<token>/',
         PasswordResetConfirmView.as_view(),
         name='auth_password_reset_confirm'),
    path('password/change/', PasswordChangeView.as_view(), name='auth_password_change'),
]
