
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from . import views_admin  # Import the admin views

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
    
    # ============ ADMIN PANEL ============
    path('admin-panel/', views_admin.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/users/', views_admin.admin_users, name='admin_users'),
    path('admin-panel/users/create/', views_admin.admin_user_create, name='admin_user_create'),
    path('admin-panel/users/<int:user_id>/edit/', views_admin.admin_user_edit, name='admin_user_edit'),
    path('admin-panel/users/<int:user_id>/delete/', views_admin.admin_user_delete, name='admin_user_delete'),
    
    path('admin-panel/students/', views_admin.admin_students, name='admin_students'),
    path('admin-panel/students/<int:student_id>/', views_admin.admin_student_detail, name='admin_student_detail'),
    
    path('admin-panel/faculties/', views_admin.admin_faculties, name='admin_faculties'),
    path('admin-panel/faculties/create/', views_admin.admin_faculty_create, name='admin_faculty_create'),
    path('admin-panel/faculties/<int:faculty_id>/edit/', views_admin.admin_faculty_edit, name='admin_faculty_edit'),
    path('admin-panel/faculties/<int:faculty_id>/delete/', views_admin.admin_faculty_delete, name='admin_faculty_delete'),
    
    path('admin-panel/programs/', views_admin.admin_programs, name='admin_programs'),
    path('admin-panel/programs/create/', views_admin.admin_program_create, name='admin_program_create'),
    path('admin-panel/programs/<int:program_id>/edit/', views_admin.admin_program_edit, name='admin_program_edit'),
    path('admin-panel/programs/<int:program_id>/delete/', views_admin.admin_program_delete, name='admin_program_delete'),
    
    path('admin-panel/applications/', views_admin.admin_applications, name='admin_applications'),
    path('admin-panel/applications/<int:app_id>/', views_admin.admin_application_detail, name='admin_application_detail'),
    
    path('admin-panel/reports/', views_admin.admin_reports, name='admin_reports'),
    path('admin-panel/audit/', views_admin.admin_audit_logs, name='admin_audit_logs'),
    path('admin-panel/settings/', views_admin.admin_settings, name='admin_settings'),
    path('admin-panel/notifications/', views_admin.admin_notifications, name='admin_notifications'),
]
