"""URL configuration for uni project."""
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('acc/', include('acc.urls')),
    path('todo/', include('todolist.urls')),
    # Not permanent, so browsers don't cache it if the landing page changes again.
    path('', RedirectView.as_view(pattern_name='todolist:home', permanent=False)),
]
