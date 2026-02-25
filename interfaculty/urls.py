from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),  # Django admin first
    path('', include('transfer.urls')),  # Your app URLs
    path('admin-panel/', include('transfer.admin_urls')),  # Your custom admin (if you have this)
    path('faq/', include('faq.urls')),  # FAQ LAST
    path('', include('django.contrib.auth.urls')),
]








if settings.DEBUG:
      urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
      urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

      path('faq/', include('faq.urls')),