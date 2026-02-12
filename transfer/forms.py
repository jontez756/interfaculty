from django import forms
from .models import Student, Program, TransferApplication, KCSE_Result
from django.contrib.auth.models import User

# ============================================
# STUDENT REGISTRATION FORM (Basic Info Only)
# ============================================
class StudentRegistrationForm(forms.ModelForm):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    first_name = forms.CharField(max_length=30, label="First Name")
    last_name = forms.CharField(max_length=30, label="Last Name")
    email = forms.EmailField(label="Email")
    
    class Meta:
        model = Student
        fields = ['admission_number', 'current_program', 'current_year', 'phone']
        widgets = {
            'admission_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., COM/0013/2023'}),
            'current_program': forms.Select(attrs={'class': 'form-control'}),
            'current_year': forms.Select(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 0712345678'}),
        }
        labels = {
            'admission_number': 'Admission Number',
            'current_program': 'Current Programme',
            'current_year': 'Current Year',
            'phone': 'Phone Number',
        }
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match!")
        
        return cleaned_data


# ============================================
# STUDENT APPLICATION FORM (KCSE & Transfer Details)
# ============================================

class StudentApplicationForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'birth_cert_no', 'id_no', 'kcse_index_no', 'kcpe_index_no',
            'mean_grade', 'aggregate_points', 'cluster_weight', 'university_cutoff',
            'address', 'kcse_slip'
        ]
        widgets = {
            'birth_cert_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 12345678'}),
            'id_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 12345678'}),
            'kcse_index_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 12345678901'}),
            'kcpe_index_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 12345678'}),
            'mean_grade': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., B+'}),
            'aggregate_points': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 42.5', 'step': '0.01'}),
            'cluster_weight': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 38.2', 'step': '0.01'}),
            'university_cutoff': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 35.5', 'step': '0.01'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Your physical address'}),
            'kcse_slip': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.jpeg,.png'}),
        }
        labels = {
            'birth_cert_no': 'Birth Cert No.',
            'id_no': 'ID No.',
            'kcse_index_no': 'KCSE Index No.',
            'kcpe_index_no': 'KCPE Index No.',
            'mean_grade': 'Mean Grade',
            'aggregate_points': 'Aggregate Points',
            'cluster_weight': 'Cluster Weight',
            'university_cutoff': 'University Cut off Point',
            'address': 'Address',
            'kcse_slip': 'Upload KCSE Result Slip (PDF/Image)',
        }





# ============================================
# TRANSFER APPLICATION FORM
# ============================================
class TransferApplicationForm(forms.ModelForm):
    class Meta:
        model = TransferApplication
        fields = ['requested_program', 'reason', 'academic_year', 'semester']
        widgets = {
            'requested_program': forms.Select(attrs={'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Explain why you want to transfer...'}),
            'academic_year': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 2025/2026'}),
            'semester': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'requested_program': 'Programme Changing To',
            'reason': 'Reason for Transfer',
            'academic_year': 'Academic Year',
            'semester': 'Semester',
        }


# ============================================
# KCSE RESULT FORM (Individual Subjects)
# ============================================
class KCSE_ResultForm(forms.ModelForm):
    class Meta:
        model = KCSE_Result
        fields = ['subject', 'grade']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Mathematics'}),
            'grade': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., B+'}),
        }