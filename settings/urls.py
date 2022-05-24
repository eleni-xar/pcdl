from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Django admin
    path('admin/', admin.site.urls),

    # User management
    path('accounts/', include('users.urls')),
    path('accounts/', include('registration.backends.default.urls')),
    # Core
    path('', include('core.urls')),
]
