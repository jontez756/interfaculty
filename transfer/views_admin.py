from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q, Count
from django.core.paginator import Paginator
from .models import Faculty, Program, Student, Profile, TransferApplication, Notification, KCSE_Result
from faq.models import Question

# ============================================
# ADMIN DASHBOARD
# ============================================
@staff_member_required
@login_required
def admin_dashboard(request):
    """Main admin dashboard with statistics"""
    
    # Statistics
    total_users = User.objects.count()
    total_students = Student.objects.count()
    total_faculties = Faculty.objects.count()
    total_programs = Program.objects.count()
    
    # Application statistics
    total_applications = TransferApplication.objects.count()
    pending_applications = TransferApplication.objects.filter(
        Q(status='pending_hod') | Q(status='pending_dean') | Q(status='pending_registrar')
    ).count()
    approved_applications = TransferApplication.objects.filter(
        Q(status='hod_approved') | Q(status='dean_approved') | Q(status='registrar_approved')
    ).count()
    rejected_applications = TransferApplication.objects.filter(
        Q(status='hod_rejected') | Q(status='dean_rejected') | Q(status='registrar_rejected')
    ).count()
    completed_applications = TransferApplication.objects.filter(status='completed').count()
    
    # Recent applications
    recent_applications = TransferApplication.objects.all().order_by('-application_date')[:10]
    
    # Faculty distribution
    faculty_stats = []
    for faculty in Faculty.objects.all():
        faculty_stats.append({
            'name': faculty.name,
            'code': faculty.code,
            'programs': Program.objects.filter(faculty=faculty).count(),
            'students': Student.objects.filter(current_program__faculty=faculty).count(),
            'applications': TransferApplication.objects.filter(
                Q(current_program__faculty=faculty) | Q(requested_program__faculty=faculty)
            ).count()
        })
    
    # User type distribution
    user_types = {
        'students': total_students,
        'hods': Profile.objects.filter(user_type='hod').count(),
        'deans': Profile.objects.filter(user_type='dean').count(),
        'registrars': Profile.objects.filter(user_type='registrar').count(),
        'admins': User.objects.filter(is_superuser=True).count(),
    }
    
    # Unread notifications
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()

    faq_count = Question.objects.count()


    context = {
        # At the top of the file with other imports
        
        'total_users': total_users,
        'total_students': total_students,
        'total_faculties': total_faculties,
        'total_programs': total_programs,
        'total_applications': total_applications,
        'pending_applications': pending_applications,
        'approved_applications': approved_applications,
        'rejected_applications': rejected_applications,
        'completed_applications': completed_applications,
        'recent_applications': recent_applications,
        'faq_count': faq_count,
        'faculty_stats': faculty_stats,
        'user_types': user_types,
        'unread_notifications': unread_notifications,
        
    }
    
    return render(request, 'admin/dashboard.html', context)


# ============================================
# USER MANAGEMENT
# ============================================
@staff_member_required
@login_required
def admin_users(request):
    """List all users with filters"""
    
    # Get filter parameters
    user_type = request.GET.get('type', '')
    search_query = request.GET.get('q', '')
    
    # Base queryset
    users = User.objects.all().order_by('-date_joined')
    
    # Apply filters
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    if user_type:
        if user_type == 'student':
            users = users.filter(profile__user_type='student')
        elif user_type == 'hod':
            users = users.filter(profile__user_type='hod')
        elif user_type == 'dean':
            users = users.filter(profile__user_type='dean')
        elif user_type == 'registrar':
            users = users.filter(profile__user_type='registrar')
        elif user_type == 'admin':
            users = users.filter(is_superuser=True)
    
    # Pagination
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'user_type': user_type,
        'search_query': search_query,
        'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
    }
    
    return render(request, 'admin/users/list.html', context)


@staff_member_required
@login_required
def admin_user_create(request):
    """Create a new user"""
    
    if request.method == 'POST':
        try:
            # Create user
            user = User.objects.create_user(
                username=request.POST.get('username'),
                password=request.POST.get('password'),
                first_name=request.POST.get('first_name', ''),
                last_name=request.POST.get('last_name', ''),
                email=request.POST.get('email', '')
            )
            
            # Set superuser if needed
            if request.POST.get('is_superuser') == 'on':
                user.is_superuser = True
                user.is_staff = True
                user.save()
            
            # Create profile
            faculty_id = request.POST.get('faculty')
            faculty = Faculty.objects.get(id=faculty_id) if faculty_id else None
            
            Profile.objects.create(
                user=user,
                user_type=request.POST.get('user_type', 'student'),
                faculty=faculty,
                phone=request.POST.get('phone', ''),
                department=request.POST.get('department', '')
            )
            
            # If student, create student record
            if request.POST.get('user_type') == 'student':
                program_id = request.POST.get('current_program')
                program = Program.objects.get(id=program_id) if program_id else None
                
                Student.objects.create(
                    user=user,
                    admission_number=request.POST.get('admission_number', ''),
                    current_program=program,
                    current_year=request.POST.get('current_year', 1),
                    phone=request.POST.get('phone', '')
                )
            
            messages.success(request, f'User {user.username} created successfully!')
            return redirect('admin_users')
            
        except Exception as e:
            messages.error(request, f'Error creating user: {str(e)}')
    
    # GET request - show form
    faculties = Faculty.objects.all()
    programs = Program.objects.all()
    
    context = {
        'faculties': faculties,
        'programs': programs,
        'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
    }
    
    return render(request, 'admin/users/create.html', context)


@staff_member_required
@login_required
def admin_user_edit(request, user_id):
    """Edit an existing user"""
    
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        try:
            # Update user
            user.username = request.POST.get('username', user.username)
            user.first_name = request.POST.get('first_name', user.first_name)
            user.last_name = request.POST.get('last_name', user.last_name)
            user.email = request.POST.get('email', user.email)
            user.is_superuser = request.POST.get('is_superuser') == 'on'
            user.is_staff = user.is_superuser
            user.save()
            
            # Update password if provided
            if request.POST.get('password'):
                user.set_password(request.POST.get('password'))
                user.save()
            
            # Update profile
            profile, created = Profile.objects.get_or_create(user=user)
            faculty_id = request.POST.get('faculty')
            profile.faculty = Faculty.objects.get(id=faculty_id) if faculty_id else None
            profile.user_type = request.POST.get('user_type', profile.user_type)
            profile.phone = request.POST.get('phone', profile.phone)
            profile.department = request.POST.get('department', profile.department)
            profile.save()
            
            messages.success(request, f'User {user.username} updated successfully!')
            return redirect('admin_users')
            
        except Exception as e:
            messages.error(request, f'Error updating user: {str(e)}')
    
    # GET request - show form
    faculties = Faculty.objects.all()
    programs = Program.objects.all()
    
    # Get student data if exists
    student = Student.objects.filter(user=user).first()
    
    context = {
        'edit_user': user,
        'profile': Profile.objects.filter(user=user).first(),
        'student': student,
        'faculties': faculties,
        'programs': programs,
        'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
    }
    
    return render(request, 'admin/users/edit.html', context)


@staff_member_required
@login_required
def admin_user_delete(request, user_id):
    """Delete a user"""
    
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        username = user.username
        user.delete()
        messages.success(request, f'User {username} deleted successfully!')
    
    return redirect('admin_users')


# ============================================
# STUDENT MANAGEMENT
# ============================================
@staff_member_required
@login_required
def admin_students(request):
    """List all students"""
    
    search_query = request.GET.get('q', '')
    faculty_filter = request.GET.get('faculty', '')
    
    students = Student.objects.all().select_related('user', 'current_program__faculty')
    
    if search_query:
        students = students.filter(
            Q(user__username__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(admission_number__icontains=search_query)
        )
    
    if faculty_filter:
        students = students.filter(current_program__faculty__id=faculty_filter)
    
    paginator = Paginator(students, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    faculties = Faculty.objects.all()
    
    context = {
        'page_obj': page_obj,
        'faculties': faculties,
        'search_query': search_query,
        'faculty_filter': faculty_filter,
        'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
    }
    
    return render(request, 'admin/students/list.html', context)


@staff_member_required
@login_required
def admin_student_detail(request, student_id):
    """View student details including KCSE results"""
    
    student = get_object_or_404(Student, id=student_id)
    applications = TransferApplication.objects.filter(student=student).order_by('-application_date')
    kcse_results = KCSE_Result.objects.filter(student=student)
    
    context = {
        'student': student,
        'applications': applications,
        'kcse_results': kcse_results,
        'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
    }
    
    return render(request, 'admin/students/detail.html', context)


# ============================================
# FACULTY MANAGEMENT
# ============================================
@staff_member_required
@login_required
def admin_faculties(request):
    """List all faculties"""
    
    faculties = Faculty.objects.all().annotate(
        program_count=Count('programs'),
        student_count=Count('programs__current_students', distinct=True)
    )
    
    context = {
        'faculties': faculties,
        'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
    }
    
    return render(request, 'admin/faculties/list.html', context)


@staff_member_required
@login_required
def admin_faculty_create(request):
    """Create a new faculty"""
    
    if request.method == 'POST':
        try:
            faculty = Faculty.objects.create(
                code=request.POST.get('code'),
                name=request.POST.get('name')
            )
            messages.success(request, f'Faculty {faculty.name} created successfully!')
            return redirect('admin_faculties')
        except Exception as e:
            messages.error(request, f'Error creating faculty: {str(e)}')
    
    context = {
        'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
    }
    
    return render(request, 'admin/faculties/create.html', context)


@staff_member_required
@login_required
def admin_faculty_edit(request, faculty_id):
    """Edit a faculty"""
    
    faculty = get_object_or_404(Faculty, id=faculty_id)
    
    if request.method == 'POST':
        try:
            faculty.code = request.POST.get('code', faculty.code)
            faculty.name = request.POST.get('name', faculty.name)
            faculty.save()
            messages.success(request, f'Faculty {faculty.name} updated successfully!')
            return redirect('admin_faculties')
        except Exception as e:
            messages.error(request, f'Error updating faculty: {str(e)}')
    
    context = {
        'faculty': faculty,
        'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
    }
    
    return render(request, 'admin/faculties/edit.html', context)


@staff_member_required
@login_required
def admin_faculty_delete(request, faculty_id):
    """Delete a faculty"""
    
    if request.method == 'POST':
        faculty = get_object_or_404(Faculty, id=faculty_id)
        name = faculty.name
        faculty.delete()
        messages.success(request, f'Faculty {name} deleted successfully!')
    
    return redirect('admin_faculties')


# ============================================
# PROGRAM MANAGEMENT
# ============================================
@staff_member_required
@login_required
def admin_programs(request):
    """List all programs"""
    
    faculty_filter = request.GET.get('faculty', '')
    search_query = request.GET.get('q', '')
    
    programs = Program.objects.all().select_related('faculty')
    
    if faculty_filter:
        programs = programs.filter(faculty__id=faculty_filter)
    
    if search_query:
        programs = programs.filter(name__icontains=search_query)
    
    faculties = Faculty.objects.all()
    
    context = {
        'programs': programs,
        'faculties': faculties,
        'faculty_filter': faculty_filter,
        'search_query': search_query,
        'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
    }
    
    return render(request, 'admin/programs/list.html', context)


@staff_member_required
@login_required
def admin_program_create(request):
    """Create a new program"""
    
    if request.method == 'POST':
        try:
            faculty = Faculty.objects.get(id=request.POST.get('faculty'))
            program = Program.objects.create(
                name=request.POST.get('name'),
                faculty=faculty
            )
            messages.success(request, f'Program {program.name} created successfully!')
            return redirect('admin_programs')
        except Exception as e:
            messages.error(request, f'Error creating program: {str(e)}')
    
    faculties = Faculty.objects.all()
    
    context = {
        'faculties': faculties,
        'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
    }
    
    return render(request, 'admin/programs/create.html', context)


@staff_member_required
@login_required
def admin_program_edit(request, program_id):
    """Edit a program"""
    
    program = get_object_or_404(Program, id=program_id)
    
    if request.method == 'POST':
        try:
            program.name = request.POST.get('name', program.name)
            program.faculty = Faculty.objects.get(id=request.POST.get('faculty'))
            program.save()
            messages.success(request, f'Program {program.name} updated successfully!')
            return redirect('admin_programs')
        except Exception as e:
            messages.error(request, f'Error updating program: {str(e)}')
    
    faculties = Faculty.objects.all()
    
    context = {
        'program': program,
        'faculties': faculties,
        'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
    }
    
    return render(request, 'admin/programs/edit.html', context)


@staff_member_required
@login_required
def admin_program_delete(request, program_id):
    """Delete a program"""
    
    if request.method == 'POST':
        program = get_object_or_404(Program, id=program_id)
        name = program.name
        program.delete()
        messages.success(request, f'Program {name} deleted successfully!')
    
    return redirect('admin_programs')


# ============================================
# APPLICATION MANAGEMENT
# ============================================
@staff_member_required
@login_required
def admin_applications(request):
    """List all applications with filters"""
    
    status_filter = request.GET.get('status', '')
    faculty_filter = request.GET.get('faculty', '')
    search_query = request.GET.get('q', '')
    
    applications = TransferApplication.objects.all().select_related(
        'student__user', 'current_program__faculty', 'requested_program__faculty'
    ).order_by('-application_date')
    
    if status_filter:
        applications = applications.filter(status=status_filter)
    
    if faculty_filter:
        applications = applications.filter(
            Q(current_program__faculty__id=faculty_filter) |
            Q(requested_program__faculty__id=faculty_filter)
        )
    
    if search_query:
        applications = applications.filter(
            Q(student__user__first_name__icontains=search_query) |
            Q(student__user__last_name__icontains=search_query) |
            Q(student__admission_number__icontains=search_query)
        )
    
    paginator = Paginator(applications, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    faculties = Faculty.objects.all()
    status_choices = TransferApplication.STATUS_CHOICES
    
    context = {
        'page_obj': page_obj,
        'faculties': faculties,
        'status_choices': status_choices,
        'status_filter': status_filter,
        'faculty_filter': faculty_filter,
        'search_query': search_query,
        'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
    }
    
    return render(request, 'admin/applications/list.html', context)


@staff_member_required
@login_required
def admin_application_detail(request, app_id):
    """View application details"""
    
    application = get_object_or_404(TransferApplication, id=app_id)
    
    if request.method == 'POST':
        # Admin override - change status
        new_status = request.POST.get('status')
        comment = request.POST.get('admin_comment', '')
        
        if new_status:
            application.status = new_status
            application.save()
            
            # Create notification
            Notification.objects.create(
                user=application.student.user,
                message=f'Admin updated your application status to: {application.get_status_display()}. Comment: {comment}',
                application=application
            )
            
            messages.success(request, f'Application status updated to {application.get_status_display()}')
        
        return redirect('admin_application_detail', app_id=app_id)
    
    context = {
        'application': application,
        'status_choices': TransferApplication.STATUS_CHOICES,
        'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
    }
    
    return render(request, 'admin/applications/detail.html', context)


# ============================================
# REPORTS
# ============================================
@staff_member_required
@login_required
def admin_reports(request):
    """Generate system reports"""
    
    report_type = request.GET.get('type', 'summary')
    date_from = request.GET.get('from', '')
    date_to = request.GET.get('to', '')
    
    context = {
        'report_type': report_type,
        'date_from': date_from,
        'date_to': date_to,
        'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
    }
    
    return render(request, 'admin/reports/index.html', context)


# ============================================
# AUDIT LOGS
# ============================================
@staff_member_required
@login_required
def admin_audit_logs(request):
    """View system audit logs"""
    
    context = {
        'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
    }
    
    return render(request, 'admin/audit/logs.html', context)


# ============================================
# SYSTEM SETTINGS
# ============================================
@staff_member_required
@login_required
def admin_settings(request):
    """System configuration"""
    
    if request.method == 'POST':
        messages.success(request, 'Settings saved successfully!')
    
    context = {
        'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
    }
    
    return render(request, 'admin/settings/index.html', context)


# ============================================
# NOTIFICATIONS
# ============================================
@staff_member_required
@login_required
def admin_notifications(request):
    """Manage system notifications"""
    
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    if request.method == 'POST':
        # Create new notification
        user_id = request.POST.get('user')
        message = request.POST.get('message')
        
        if user_id and message:
            target_user = User.objects.get(id=user_id)
            Notification.objects.create(
                user=target_user,
                message=message
            )
            messages.success(request, 'Notification sent successfully!')
    
    context = {
        'notifications': notifications,
        'users': User.objects.filter(is_active=True),
        'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
    }
    
    return render(request, 'admin/notifications/index.html', context)