from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from transfer import views 


urlpatterns = [
    path('admin/', admin.site.urls),  
    path('', include('transfer.urls')),  
    #path('admin-panel/', include('transfer.admin_urls')),  
    path('', include('django.contrib.auth.urls')),
    path('faq/', views.faq_view, name='faq'),
    path('simple-faq/', views.simple_faq, name='simple_faq'),
    
]


if settings.DEBUG:
      urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
      urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

      #path('faq/', include('faq.urls')),

path('simple-faq/', views.simple_faq, name='simple_faq'),