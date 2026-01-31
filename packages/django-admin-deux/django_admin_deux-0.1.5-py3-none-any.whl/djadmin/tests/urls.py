"""URL configuration for core-only integration tests."""

from django.urls import include, path

from djadmin import site

urlpatterns = [
    path('djadmin/', include(site.urls)),
    path('accounts/', include('django.contrib.auth.urls')),  # Required for authentication
]

# Debug toolbar URLs (optional)
try:
    import debug_toolbar

    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
except ImportError:
    pass
