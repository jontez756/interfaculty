from django.contrib import admin
from .models import Faculty, Program, Profile, Student, TransferApplication, Notification

@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ['code', 'name']
    search_fields = ['code', 'name']
    ordering = ['code']

@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ['name', 'faculty']
    list_filter = ['faculty']
    search_fields = ['name']
    ordering = ['faculty', 'name']

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'user_type', 'faculty']
    list_filter = ['user_type', 'faculty']
    search_fields = ['user__username', 'user__email']

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['admission_number', 'user', 'current_program', 'current_year']
    list_filter = ['current_program']
    search_fields = ['admission_number', 'user__username']

@admin.register(TransferApplication)
class TransferApplicationAdmin(admin.ModelAdmin):
    list_display = ['student', 'current_program', 'requested_program', 'status', 'application_date']
    list_filter = ['status', 'academic_year', 'semester']
    search_fields = ['student__admission_number', 'student__user__username']
    readonly_fields = ['application_date', 'last_updated']
    list_per_page = 25

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'message', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['user__username', 'message']
    readonly_fields = ['created_at']