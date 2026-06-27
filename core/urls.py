from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls')),
    path('fitness/', include('apps.fitness.urls')),
    path('', include('apps.gyms.urls')),
    path('bookings/', include('apps.bookings.urls')),
    path('dashboard/', include('apps.dashboard.urls')),
    path('notifications/', include('apps.notifications.urls')),
    path('reviews/', include('apps.reviews.urls')),
    path('control/', include('apps.controlpanel.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
