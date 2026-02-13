from django.db import models
from django.contrib.auth.models import User


# FACULTY MODEL
class Faculty(models.Model):
    FACULTY_CHOICES = [
        ('SESS', 'School of Education & Social Sciences'),
        ('SOBE', 'School of Business & Economics'),
        ('SCIT', 'School of Computing & Information Technology'),
        ('SOS', 'School of Science'),
        ('SOHES', 'School of Health Sciences'),
    ]
    
    name = models.CharField(max_length=10, choices=FACULTY_CHOICES, unique=True)
    code = models.CharField(max_length=100)

    
    
    def __str__(self):
        return f"{self.code}: {self.name}"  # Shows "SESS: School of Education & Social Sciences"

# PROGRAM MODEL - FIXED __str__ METHOD
class Program(models.Model):
    name = models.CharField(max_length=100)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='programs')
    
    def __str__(self):
        return f"{self.name} ({self.faculty.code})"  # FIXED: self.faculty.code, NOT self.code

# USER PROFILE MODEL
User.profile = property(lambda u: Profile.objects.get_or_create(user=u)[0])
class Profile(models.Model):
    USER_TYPES = [
        ('student', 'Student'),
        ('hod', 'Head of Department'),
        ('dean', 'Dean'),
        ('registrar', 'Registrar'),
        ('admin', 'Admin'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=20, choices=USER_TYPES)
    profile_pic = models.ImageField(upload_to='profiles/', null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)
    faculty = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, blank=True)
    department = models.CharField(max_length=100, null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.user_type}"
    profile_pic = models.ImageField(upload_to='profiles/', null=True, blank=True)

# STUDENT MODEL - FIXED: MOVE Program class ABOVE this
class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    admission_number = models.CharField(max_length=20, unique=True)
    current_program = models.ForeignKey('Program', on_delete=models.SET_NULL, null=True, related_name='current_students')
    current_year = models.IntegerField()
    phone = models.CharField(max_length=15)
    address = models.TextField(blank=True, null=True)
    kcse_slip = models.FileField(
        upload_to='kcse_slips/%Y/%m/%d/', 
        blank=True, 
        null=True
    )
    
    # NEW FIELDS - Personal Details
    birth_cert_no = models.CharField(max_length=50, blank=True, null=True)
    id_no = models.CharField(max_length=20, blank=True, null=True)
    kcse_index_no = models.CharField(max_length=30, blank=True, null=True)
    kcpe_index_no = models.CharField(max_length=30, blank=True, null=True)
    
    # NEW FIELDS - KCSE Summary
    mean_grade = models.CharField(max_length=5, blank=True, null=True)
    aggregate_points = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    cluster_weight = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    university_cutoff = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    
    # NEW FIELD - KCSE Slip Upload
    kcse_slip = models.FileField(upload_to='kcse_slips/', blank=True, null=True)
    
    def __str__(self):
        return f"{self.admission_number} - {self.user.get_full_name()}"


    # KCSE RESULT MODEL
class KCSE_Result(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='kcse_results')
    subject = models.CharField(max_length=100)
    grade = models.CharField(max_length=5)
    
    def __str__(self):
        return f"{self.subject}: {self.grade}"

    
    def __str__(self):
        return f"{self.subject}: {self.grade}"
birth_cert_no = models.CharField(max_length=50, blank=True, null=True)
id_no = models.CharField(max_length=20, blank=True, null=True)
kcse_index_no = models.CharField(max_length=30)
kcpe_index_no = models.CharField(max_length=30, blank=True, null=True)
mean_grade = models.CharField(max_length=5)
aggregate_points = models.DecimalField(max_digits=5, decimal_places=2)
cluster_weight = models.DecimalField(max_digits=5, decimal_places=2)
university_cutoff = models.DecimalField(max_digits=5, decimal_places=2)
kcse_slip = models.FileField(upload_to='kcse_slips/', blank=True, null=True)
# TRANSFER APPLICATION MODEL
class TransferApplication(models.Model):
    STATUS_CHOICES = [
        ('pending_hod', 'Pending HOD Review'),
        ('hod_approved', 'HOD Approved'),
        ('hod_rejected', 'HOD Rejected'),
        ('pending_dean', 'Pending Dean Review'),
        ('dean_approved', 'Dean Approved'),
        ('dean_rejected', 'Dean Rejected'),
        ('pending_registrar', 'Pending Registrar Review'),
        ('registrar_approved', 'Registrar Approved'),
        ('registrar_rejected', 'Registrar Rejected'),
        ('completed', 'Completed'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='applications')
    current_program = models.ForeignKey('Program', on_delete=models.SET_NULL, null=True, related_name='transfer_from')
    requested_program = models.ForeignKey('Program', on_delete=models.SET_NULL, null=True, related_name='transfer_to')
    reason = models.TextField()
    academic_year = models.CharField(max_length=20)
    semester = models.IntegerField(choices=[(1, 'Semester 1'), (2, 'Semester 2')])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_hod')
    application_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    hod_comment = models.TextField(null=True, blank=True)
    dean_comment = models.TextField(null=True, blank=True)
    registrar_comment = models.TextField(null=True, blank=True)
    new_admission_number = models.CharField(max_length=20, null=True, blank=True)
    
    def __str__(self):
        return f"{self.student.admission_number} - {self.requested_program}"

# NOTIFICATION MODEL
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    application = models.ForeignKey(TransferApplication, on_delete=models.CASCADE, null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.message[:50]}"



