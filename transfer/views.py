from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Student, Program, TransferApplication, Notification, Profile, Faculty, KCSE_Result
from .forms import StudentRegistrationForm, StudentApplicationForm, TransferApplicationForm
from django.db.models import Q
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
import csv
import json
from datetime import datetime
from faq.models import Question

from django.http import HttpResponse

def test_view(request):
    return HttpResponse("Test view is working!")
# ============================================
# HOME PAGE
# ============================================
def home(request):
    return render(request, 'home.html')

def faq_view(request):
    questions = Question.objects.filter(status=1).select_related('category')
    return render(request, 'faq/questions_list.html', {'questions': questions})


# ============================================
# CUSTOM LOGOUT
# ============================================
def custom_logout(request):
    logout(request)
    return redirect('login')


# ============================================
# DASHBOARD REDIRECT - Based on user type
# ============================================
@login_required
def dashboard_redirect(request):
    """Redirect users to their appropriate dashboard based on user type"""
    try:
        profile = Profile.objects.get(user=request.user)
        
        if profile.user_type == 'student':
            return redirect('student_dashboard')
        elif profile.user_type == 'hod':
            return redirect('hod_dashboard')
        elif profile.user_type == 'dean':
            return redirect('dean_dashboard')
        elif profile.user_type == 'registrar':
            return redirect('registrar_dashboard')
        elif profile.user_type == 'admin':
            return redirect('/admin/')
        else:
            return redirect('home')
    except Profile.DoesNotExist:
        return redirect('register_student')


# ============================================
# STUDENT REGISTRATION (Basic Info Only)
# ============================================
def register_student(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            # Create user
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                email=form.cleaned_data['email']
            )
            
            # Create student profile
            student = form.save(commit=False)
            student.user = user
            student.save()
            
            # Create profile for user type
            Profile.objects.create(
                user=user,
                user_type='student',
                phone=student.phone,
                faculty=student.current_program.faculty
            )
            
            messages.success(request, 'Registration successful! You can now login and complete your application.')
            return redirect('login')
    else:
        form = StudentRegistrationForm()
    
    return render(request, 'register_student.html', {'form': form})


# ============================================
# STUDENT DASHBOARD
# ============================================

from django.http import HttpResponse


@login_required
def student_dashboard(request):
    try:
        # Check if user is a student
        profile = Profile.objects.get(user=request.user)
        if profile.user_type != 'student':
            messages.error(request, 'Access denied. Student dashboard only.')
            return redirect('dashboard_redirect')
            
        student = Student.objects.get(user=request.user)
        # THIS LINE IS CRITICAL - make sure it's there
        applications = TransferApplication.objects.filter(student=student).order_by('-application_date')
        notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')
        
        # Mark notifications as read
        for notification in notifications:
            notification.is_read = True
            notification.save()
        
        # Check if student has completed their profile
        has_completed_profile = all([
            student.kcse_index_no,
            student.mean_grade,
            student.kcse_slip
        ])
        
    except Student.DoesNotExist:
        messages.warning(request, 'Please complete your student profile first.')
        return redirect('student_application_form')
    except Profile.DoesNotExist:
        messages.error(request, 'Profile not found. Please contact admin.')
        return redirect('home')
    
    context = {
        'student': student,
        'applications': applications,  # This must be passed to template
        'notifications': notifications,
        'has_completed_profile': has_completed_profile,
    }
    return render(request, 'student_dashboard.html', context)





# ============================================
# STUDENT APPLICATION FORM (KCSE & Transfer Details)
# ============================================
@login_required
def student_application_form(request):
    """Student fills detailed KCSE and transfer application"""
    try:
        # Check if user is a student
        profile = Profile.objects.get(user=request.user)
        if profile.user_type != 'student':
            messages.error(request, 'Access denied. Student only.')
            return redirect('home')
            
        student = Student.objects.get(user=request.user)
        
        # Check if already has pending application
        existing_application = TransferApplication.objects.filter(
            student=student,
            status__in=['pending_hod', 'hod_approved', 'dean_approved']
        ).first()
        
        if existing_application:
            messages.warning(request, 'You already have a pending transfer application.')
            return redirect('student_dashboard')
        
    except (Student.DoesNotExist, Profile.DoesNotExist):
        return redirect('register_student')
    
    if request.method == 'POST':
        # Update student with KCSE details
        student.birth_cert_no = request.POST.get('birth_cert_no')
        student.id_no = request.POST.get('id_no')
        student.kcse_index_no = request.POST.get('kcse_index_no')
        student.kcpe_index_no = request.POST.get('kcpe_index_no')
        student.mean_grade = request.POST.get('mean_grade')
        student.aggregate_points = request.POST.get('aggregate_points')
        student.cluster_weight = request.POST.get('cluster_weight')
        student.university_cutoff = request.POST.get('university_cutoff')
        student.address = request.POST.get('address')
        
        # Handle KCSE slip upload
        if 'kcse_slip' in request.FILES:
            student.kcse_slip = request.FILES['kcse_slip']
        
        student.save()
        
        # Save KCSE subject results
        KCSE_Result.objects.filter(student=student).delete()  # Clear old results
        for i in range(1, 20):
            subject = request.POST.get(f'subject_{i}')
            grade = request.POST.get(f'grade_{i}')
            if subject and grade:
                KCSE_Result.objects.create(
                    student=student,
                    subject=subject,
                    grade=grade
                )
        
        # Create transfer application
        application = TransferApplication.objects.create(
            student=student,
            current_program=student.current_program,
            requested_program_id=request.POST.get('requested_program'),
            reason=request.POST.get('reason'),
            academic_year=request.POST.get('academic_year'),
            semester=request.POST.get('semester'),
            status='pending_hod'
        )
        
        # Notify HOD (University HOD - no faculty)
        hod_profile = Profile.objects.filter(
            user_type='hod',
            faculty=None
        ).first()
        
        if hod_profile:
            Notification.objects.create(
                user=hod_profile.user,
                message=f"New transfer application from {student.user.get_full_name()} - {student.current_program.name} to {application.requested_program.name}",
                application=application
            )
        
        messages.success(request, 'Transfer application submitted successfully!')
        return redirect('student_dashboard')
    
    # Get programs for dropdown (exclude current faculty)
    programs = Program.objects.exclude(faculty=student.current_program.faculty)
    
    context = {
        'student': student,
        'programs': programs,
    }
    return render(request, 'student_application_form.html', context)


# ============================================
# HOD DASHBOARD - University HOD (No Faculty)
# ============================================
@login_required
def hod_dashboard(request):
    try:
        # Get HOD profile
        profile = Profile.objects.get(user=request.user, user_type='hod')
        
        # University HOD (no faculty assigned) - sees ALL applications
        if profile.faculty is None:
            pending_applications = TransferApplication.objects.filter(
                status='pending_hod'
            ).order_by('-application_date')
            
            all_applications = TransferApplication.objects.all().order_by('-application_date')
            faculty_filter = "All Faculties"
        else:
            # Faculty-specific HOD (fallback)
            pending_applications = TransferApplication.objects.filter(
                current_program__faculty=profile.faculty,
                status='pending_hod'
            ).order_by('-application_date')
            
            all_applications = TransferApplication.objects.filter(
                current_program__faculty=profile.faculty
            ).order_by('-application_date')
            faculty_filter = profile.faculty.name
        
        # Get unread notifications
        notifications = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).order_by('-created_at')
        
        # Mark notifications as read
        for notification in notifications:
            notification.is_read = True
            notification.save()
        
        context = {
            'faculty': faculty_filter,
            'pending_applications': pending_applications,
            'all_applications': all_applications,
            'notifications': notifications,
            'pending_count': pending_applications.count(),
            'is_university_hod': profile.faculty is None,
        }
        return render(request, 'hod_dashboard.html', context)
        
    except Profile.DoesNotExist:
        messages.error(request, 'You are not authorized as a HOD.')
        return redirect('home')


# ============================================
# HOD REVIEW APPLICATION
# ============================================
@login_required
def review_application(request, app_id):
    try:
        # Check if user is HOD
        profile = Profile.objects.get(user=request.user)
        if profile.user_type != 'hod':
            messages.error(request, 'Access denied. Only HOD can review applications.')
            return redirect('dashboard_redirect')
        
        application = TransferApplication.objects.get(id=app_id)
        
        # University HOD (no faculty) can review ANY application
        if profile.faculty is not None:
            # Faculty HOD can only review their own faculty
            if application.current_program.faculty != profile.faculty:
                messages.error(request, f'This application is for {application.current_program.faculty.name}. You are HOD of {profile.faculty.name}.')
                return redirect('hod_dashboard')
        
        if request.method == 'POST':
            action = request.POST.get('action')
            comment = request.POST.get('comment', '')
            
            if action == 'approve':
                application.status = 'hod_approved'
                application.hod_comment = comment
                messages.success(request, 'Application approved! Sent to Dean.')
                
                # Notify student
                Notification.objects.create(
                    user=application.student.user,
                    message=f'Your transfer application has been approved by HOD.',
                    application=application
                )
                
                # Notify dean of the requested faculty
                dean_profile = Profile.objects.filter(
                    user_type='dean',
                    faculty=application.requested_program.faculty
                ).first()
                if dean_profile:
                    Notification.objects.create(
                        user=dean_profile.user,
                        message=f'New transfer application pending for {application.requested_program.faculty.name} from {application.student.user.get_full_name()}',
                        application=application
                    )
                
            elif action == 'reject':
                application.status = 'hod_rejected'
                application.hod_comment = comment
                messages.success(request, 'Application rejected.')
                
                # Notify student
                Notification.objects.create(
                    user=application.student.user,
                    message=f'Your transfer application has been rejected by HOD. Reason: {comment}',
                    application=application
                )
            
            application.save()
            return redirect('hod_dashboard')
            
    except Profile.DoesNotExist:
        messages.error(request, 'Profile not found.')
        return redirect('home')
    except TransferApplication.DoesNotExist:
        messages.error(request, 'Application not found.')
        return redirect('hod_dashboard')
    
    context = {
        'application': application,
    }
    return render(request, 'review_application.html', context)


# ============================================
# DEAN DASHBOARD
# ============================================
@login_required
def dean_dashboard(request):
    try:
        # Get Dean profile
        profile = Profile.objects.get(user=request.user, user_type='dean')
        
        # IMPORTANT: Check if faculty exists
        if not profile.faculty:
            messages.error(request, 'Your dean profile has no faculty assigned. Contact administrator.')
            return redirect('home')
        
        dean_faculty = profile.faculty
        
        # Get applications for THIS DEAN'S FACULTY (where students want to transfer TO this faculty)
        pending_applications = TransferApplication.objects.filter(
            requested_program__faculty=dean_faculty,
            status='hod_approved'  # Only show HOD approved applications
        ).order_by('-application_date')
        
        # All applications for this faculty
        all_applications = TransferApplication.objects.filter(
            requested_program__faculty=dean_faculty
        ).order_by('-application_date')
        
        # Get unread notifications
        notifications = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).order_by('-created_at')
        
        # Mark notifications as read
        for notification in notifications:
            notification.is_read = True
            notification.save()
        
        context = {
            'faculty': dean_faculty,
            'pending_applications': pending_applications,
            'all_applications': all_applications,
            'notifications': notifications,
            'pending_count': pending_applications.count(),
        }
        return render(request, 'dean_dashboard.html', context)
        
    except Profile.DoesNotExist:
        messages.error(request, 'You are not authorized as a Dean.')
        return redirect('home')


# ============================================
# DEAN REVIEW APPLICATION
# ============================================
@login_required
def dean_review(request, app_id):
    try:
        profile = Profile.objects.get(user=request.user, user_type='dean')
        
        if not profile.faculty:
            messages.error(request, 'Your dean profile has no faculty assigned.')
            return redirect('dean_dashboard')
        
        application = TransferApplication.objects.get(id=app_id)
        
        # Verify this application is for this dean's faculty
        if application.requested_program.faculty != profile.faculty:
            messages.error(request, 'You can only review applications for your faculty.')
            return redirect('dean_dashboard')
        
        # Verify application is HOD approved
        if application.status != 'hod_approved':
            messages.error(request, 'This application is not ready for dean review.')
            return redirect('dean_dashboard')
        
        if request.method == 'POST':
            action = request.POST.get('action')
            comment = request.POST.get('comment', '')
            
            if action == 'approve':
                application.status = 'dean_approved'
                application.dean_comment = comment
                messages.success(request, 'Application approved and sent to Registrar!')
                
                # Notify student
                Notification.objects.create(
                    user=application.student.user,
                    message=f'Your transfer application has been approved by the Dean of {profile.faculty.name}. Sent to Registrar for final approval.',
                    application=application
                )
                
                # Notify registrar
                registrar_profile = Profile.objects.filter(user_type='registrar').first()
                if registrar_profile:
                    Notification.objects.create(
                        user=registrar_profile.user,
                        message=f'New application from {application.student.user.get_full_name()} approved by Dean. Pending your review.',
                        application=application
                    )
                
            elif action == 'reject':
                application.status = 'dean_rejected'
                application.dean_comment = comment
                messages.success(request, 'Application rejected.')
                
                # Notify student
                Notification.objects.create(
                    user=application.student.user,
                    message=f'Your transfer application has been rejected by the Dean. Reason: {comment}',
                    application=application
                )
            
            application.save()
            return redirect('dean_dashboard')
            
    except Profile.DoesNotExist:
        messages.error(request, 'You are not authorized as a Dean.')
        return redirect('home')
    except TransferApplication.DoesNotExist:
        messages.error(request, 'Application not found.')
        return redirect('dean_dashboard')
    
    context = {
        'application': application,
        'faculty': profile.faculty
    }
    return render(request, 'dean_review.html', context)


# ============================================
# REGISTRAR DASHBOARD
# ============================================
@login_required
def registrar_dashboard(request):
    """Registrar dashboard with pending and completed transfers"""
    try:
        profile = Profile.objects.get(user=request.user)
        if profile.user_type != 'registrar':
            messages.error(request, 'Access denied. Registrar only.')
            return redirect('home')
    except Profile.DoesNotExist:
        return redirect('home')
    
    # Get dean-approved applications pending registrar review
    pending_applications = TransferApplication.objects.filter(
        status='dean_approved'
    ).order_by('-application_date')
    
    # Get completed transfers
    completed_transfers = TransferApplication.objects.filter(
        status='completed'
    ).order_by('-last_updated')
    
    # Get unread notifications
    notifications = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).order_by('-created_at')
    
    # Mark notifications as read
    for notification in notifications:
        notification.is_read = True
        notification.save()
    
    context = {
        'pending_applications': pending_applications,
        'completed_transfers': completed_transfers,
        'notifications': notifications,
        'pending_count': pending_applications.count(),
    }
    return render(request, 'registrar_dashboard.html', context)


# ============================================
# REGISTRAR REVIEW APPLICATION
# ============================================
@login_required
def registrar_review(request, app_id):
    """Registrar reviews dean-approved applications and issues new admission number"""
    try:
        profile = Profile.objects.get(user=request.user)
        if profile.user_type != 'registrar':
            messages.error(request, 'Access denied. Registrar only.')
            return redirect('home')
        
        application = TransferApplication.objects.get(id=app_id)
        
        # Only allow review of dean-approved applications
        if application.status != 'dean_approved':
            messages.error(request, 'This application is not ready for registrar review.')
            return redirect('registrar_dashboard')
        
        if request.method == 'POST':
            action = request.POST.get('action')
            comment = request.POST.get('comment', '')
            new_admission = request.POST.get('new_admission_number', '')
            
            if action == 'approve':
                application.status = 'completed'
                application.registrar_comment = comment
                application.new_admission_number = new_admission
                messages.success(request, 'Transfer completed! New admission number issued.')
                
                # Update student's program and admission number
                student = application.student
                student.current_program = application.requested_program
                student.admission_number = new_admission
                student.save()
                
                # Notify student
                Notification.objects.create(
                    user=application.student.user,
                    message=f'✅ Your transfer has been approved! New admission number: {new_admission}. You are now in {application.requested_program.name}.',
                    application=application
                )
                
                # Notify HOD of new faculty
                hod_profile = Profile.objects.filter(
                    user_type='hod',
                    faculty=application.requested_program.faculty
                ).first()
                if hod_profile:
                    Notification.objects.create(
                        user=hod_profile.user,
                        message=f'Student {application.student.user.get_full_name()} has transferred to your faculty. New admission: {new_admission}',
                        application=application
                    )
                
                # Notify Dean of new faculty
                dean_profile = Profile.objects.filter(
                    user_type='dean',
                    faculty=application.requested_program.faculty
                ).first()
                if dean_profile:
                    Notification.objects.create(
                        user=dean_profile.user,
                        message=f'Student {application.student.user.get_full_name()} has been approved by Registrar and joined your faculty.',
                        application=application
                    )
                
            elif action == 'reject':
                application.status = 'registrar_rejected'
                application.registrar_comment = comment
                messages.success(request, 'Application rejected.')
                
                # Notify student
                Notification.objects.create(
                    user=application.student.user,
                    message=f'❌ Your transfer application has been rejected by the Registrar. Reason: {comment}',
                    application=application
                )
            
            application.save()
            return redirect('registrar_dashboard')
            
    except Profile.DoesNotExist:
        messages.error(request, 'Profile not found.')
        return redirect('home')
    except TransferApplication.DoesNotExist:
        messages.error(request, 'Application not found.')
        return redirect('registrar_dashboard')
    
    context = {
        'application': application,
    }
    return render(request, 'registrar_review.html', context) 
#============================================  
      # REPORT DASHBOARD
# ============================================
@login_required
def report_dashboard(request):
    """Central report dashboard - different views per user type"""
    try:
        profile = Profile.objects.get(user=request.user)
        
        # Get counts based on user type
        if profile.user_type == 'hod' and profile.faculty is None:
            # University HOD - sees all
            total_applications = TransferApplication.objects.count()
            pending = TransferApplication.objects.filter(status='pending_hod').count()
            approved = TransferApplication.objects.filter(status='hod_approved').count()
            rejected = TransferApplication.objects.filter(status='hod_rejected').count()
            completed = TransferApplication.objects.filter(status='completed').count()
            faculties = Faculty.objects.all()
            
        elif profile.user_type == 'dean':
            # Dean - sees only their faculty
            total_applications = TransferApplication.objects.filter(
                requested_program__faculty=profile.faculty
            ).count()
            pending = TransferApplication.objects.filter(
                requested_program__faculty=profile.faculty,
                status='hod_approved'
            ).count()
            approved = TransferApplication.objects.filter(
                requested_program__faculty=profile.faculty,
                status='dean_approved'
            ).count()
            rejected = TransferApplication.objects.filter(
                requested_program__faculty=profile.faculty,
                status='dean_rejected'
            ).count()
            completed = TransferApplication.objects.filter(
                requested_program__faculty=profile.faculty,
                status='completed'
            ).count()
            faculties = [profile.faculty]
            
        elif profile.user_type == 'registrar':
            # Registrar - sees all completed and pending
            total_applications = TransferApplication.objects.count()
            pending = TransferApplication.objects.filter(status='dean_approved').count()
            completed = TransferApplication.objects.filter(status='completed').count()
            rejected = TransferApplication.objects.filter(status='registrar_rejected').count()
            faculties = Faculty.objects.all()
            
        elif profile.user_type == 'student':
            # Student - sees only their own
            student = Student.objects.get(user=request.user)
            total_applications = TransferApplication.objects.filter(student=student).count()
            applications = TransferApplication.objects.filter(student=student)
            pending = applications.filter(status__contains='pending').count()
            approved = applications.filter(status__contains='approved').count()
            rejected = applications.filter(status__contains='rejected').count()
            faculties = []
            
        else:
            messages.error(request, 'Access denied.')
            return redirect('home')
        
        context = {
            'user_type': profile.user_type,
            'total_applications': total_applications,
            'pending': pending,
            'approved': approved,
            'rejected': rejected,
            'completed': completed,
            'faculties': faculties,
        }
        return render(request, 'report_dashboard.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading reports: {str(e)}')
        return redirect('home')


# ============================================
# EXPORT TO CSV
# ============================================
@login_required
def export_applications_csv(request):
    """Export applications data to CSV"""
    try:
        profile = Profile.objects.get(user=request.user)
        
        # Filter based on user type
        if profile.user_type == 'hod' and profile.faculty is None:
            applications = TransferApplication.objects.all()
        elif profile.user_type == 'dean':
            applications = TransferApplication.objects.filter(
                requested_program__faculty=profile.faculty
            )
        elif profile.user_type == 'registrar':
            applications = TransferApplication.objects.all()
        elif profile.user_type == 'student':
            student = Student.objects.get(user=request.user)
            applications = TransferApplication.objects.filter(student=student)
        else:
            messages.error(request, 'Access denied.')
            return redirect('report_dashboard')
        
        # Create HttpResponse with CSV header
        response = HttpResponse(content_type='text/csv')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        response['Content-Disposition'] = f'attachment; filename="transfer_applications_{timestamp}.csv"'
        
        writer = csv.writer(response)
        # Write header
        writer.writerow([
            'Application ID', 'Date', 'Student Name', 'Admission Number',
            'Current Program', 'Current Faculty', 'Requested Program',
            'Requested Faculty', 'Status', 'Academic Year', 'Semester',
            'HOD Comment', 'Dean Comment', 'Registrar Comment',
            'New Admission Number'
        ])
        
        # Write data rows
        for app in applications:
            writer.writerow([
                app.id,
                app.application_date.strftime('%Y-%m-%d %H:%M'),
                app.student.user.get_full_name(),
                app.student.admission_number,
                app.current_program.name,
                app.current_program.faculty.name,
                app.requested_program.name,
                app.requested_program.faculty.name,
                app.get_status_display(),
                app.academic_year,
                app.get_semester_display(),
                app.hod_comment or '',
                app.dean_comment or '',
                app.registrar_comment or '',
                app.new_admission_number or ''
            ])
        
        return response
        
    except Exception as e:
        messages.error(request, f'Error exporting data: {str(e)}')
        return redirect('report_dashboard')


# ============================================
# EXPORT TO PDF (Simple HTML version)
# ============================================
@login_required
def export_applications_pdf(request):
    """Export applications data to printable HTML/PDF"""
    try:
        profile = Profile.objects.get(user=request.user)
        
        # Filter based on user type
        if profile.user_type == 'hod' and profile.faculty is None:
            applications = TransferApplication.objects.all()
            title = "All Applications Report"
        elif profile.user_type == 'dean':
            applications = TransferApplication.objects.filter(
                requested_program__faculty=profile.faculty
            )
            title = f"{profile.faculty.name} - Applications Report"
        elif profile.user_type == 'registrar':
            applications = TransferApplication.objects.all()
            title = "Registrar - Complete Applications Report"
        elif profile.user_type == 'student':
            student = Student.objects.get(user=request.user)
            applications = TransferApplication.objects.filter(student=student)
            title = f"{student.user.get_full_name()} - My Applications Report"
        else:
            messages.error(request, 'Access denied.')
            return redirect('report_dashboard')
        
        context = {
            'applications': applications,
            'title': title,
            'generated_date': datetime.now(),
            'user': request.user,
            'user_type': profile.user_type,
        }
        
        # Render HTML template
        html_string = render_to_string('report_pdf.html', context)
        return HttpResponse(html_string)
        
    except Exception as e:
        messages.error(request, f'Error generating report: {str(e)}')
        return redirect('report_dashboard')


# ============================================
# FACULTY WISE REPORT
# ============================================
@login_required
def faculty_report(request, faculty_code=None):
    """Generate report for specific faculty"""
    try:
        profile = Profile.objects.get(user=request.user)
        
        # Check permissions
        if profile.user_type not in ['hod', 'registrar', 'admin']:
            messages.error(request, 'Access denied.')
            return redirect('report_dashboard')
        
        if faculty_code:
            faculty = Faculty.objects.get(code=faculty_code)
            applications = TransferApplication.objects.filter(
                Q(current_program__faculty=faculty) | 
                Q(requested_program__faculty=faculty)
            )
        else:
            faculty = None
            applications = TransferApplication.objects.all()
        
        context = {
            'faculty': faculty,
            'applications': applications,
            'total': applications.count(),
            'pending': applications.filter(status__contains='pending').count(),
            'approved': applications.filter(status__contains='approved').count(),
            'rejected': applications.filter(status__contains='rejected').count(),
            'completed': applications.filter(status='completed').count(),
        }
        
        return render(request, 'faculty_report.html', context)
        
    except Faculty.DoesNotExist:
        messages.error(request, 'Faculty not found.')
        return redirect('report_dashboard')
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('report_dashboard')


# ============================================
# STUDENT PERFORMANCE REPORT (For HOD/Registrar)
# ============================================
@login_required
def student_academic_report(request, student_id):
    """View student's academic details and KCSE results"""
    try:
        profile = Profile.objects.get(user=request.user)
        
        # Only HOD, Dean, Registrar can view
        if profile.user_type not in ['hod', 'dean', 'registrar', 'admin']:
            messages.error(request, 'Access denied.')
            return redirect('home')
        
        student = Student.objects.get(id=student_id)
        applications = TransferApplication.objects.filter(student=student)
        kcse_results = KCSE_Result.objects.filter(student=student)
        
        context = {
            'student': student,
            'applications': applications,
            'kcse_results': kcse_results,
        }
        return render(request, 'student_academic_report.html', context)
        
    except Student.DoesNotExist:
        messages.error(request, 'Student not found.')
        return redirect('report_dashboard')
    
    def media_test(request):
       return render(request, 'media_test.html')