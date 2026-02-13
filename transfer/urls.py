from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Home
    path('', views.home, name='home'),
    
    # Authentication
    path('register/', views.register_student, name='register_student'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html', redirect_authenticated_user=True), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    
    # Redirects
    path('dashboard-redirect/', views.dashboard_redirect, name='dashboard_redirect'),
    path('accounts/profile/', views.dashboard_redirect, name='profile_redirect'),
    
    # Student
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('apply/', views.student_application_form, name='student_application_form'),
    
    # HOD
    path('hod-dashboard/', views.hod_dashboard, name='hod_dashboard'),
    path('review/<int:app_id>/', views.review_application, name='review_application'),
    
    # DEAN
    path('dean-dashboard/', views.dean_dashboard, name='dean_dashboard'),
    path('dean-review/<int:app_id>/', views.dean_review, name='dean_review'),
    
    # REGISTRAR
    path('registrar-dashboard/', views.registrar_dashboard, name='registrar_dashboard'),
    path('registrar-review/<int:app_id>/', views.registrar_review, name='registrar_review'),
    
    # ============ REPORTS ============
    path('reports/', views.report_dashboard, name='report_dashboard'),
    path('reports/export/csv/', views.export_applications_csv, name='export_applications_csv'),
    path('reports/export/pdf/', views.export_applications_pdf, name='export_applications_pdf'),
    path('reports/faculty/<str:faculty_code>/', views.faculty_report, name='faculty_report'),
    path('reports/student/<int:student_id>/', views.student_academic_report, name='student_academic_report'),
    path('test/', views.test_view, name='test_view'),
]





