from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from transfer import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('transfer.urls')),
    path('', include('django.contrib.auth.urls')),  # ← Added comma at the end
    path('faq/', views.simple_faq, name='faq'),
    
    # Password Reset URLs (Code-based)
    path('password-reset/', views.password_reset_request, name='password_reset'),
    path('password-reset/verify/', views.password_reset_verify, name='password_reset_verify'),
    path('password-reset/confirm/', views.password_reset_confirm, name='password_reset_confirm'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)