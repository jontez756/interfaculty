



from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from transfer import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('transfer.urls')),
    path('', include('django.contrib.auth.urls')),
    path('faq/', views.simple_faq, name='faq'),  # ← Changed to simple_faq
    # path('faq/', include('faq.urls')),  # ← Comment this out
     path('', include('django.contrib.auth.urls'))
     
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)