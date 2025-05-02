from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = 'STUDENT', 'Student'
        PROFESSIONAL = 'PROFESSIONAL', 'Professional'
        COUNSELOR = 'COUNSELOR', 'Counselor'
        ADMIN = 'ADMIN', 'Admin'
    
    name = models.CharField(max_length=255, blank=True)  # Added name field
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT
    )
    is_verified = models.BooleanField(default=False)
    is_profile_complete = models.BooleanField(default=False)
    
    # Add related_name to resolve the clashes
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='api_user_set',
        related_query_name='api_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='api_user_set',
        related_query_name='api_user',
    )

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    about = models.TextField(null=True, blank=True)
    photo_url = models.CharField(max_length=255, null=True, blank=True)
    technical_skills = ArrayField(models.CharField(max_length=100), default=list)
    soft_skills = ArrayField(models.CharField(max_length=100), default=list)
    languages = ArrayField(models.CharField(max_length=50), default=list)
    interests = ArrayField(models.CharField(max_length=100), default=list)
    career_goals = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Education(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='education')
    degree = models.CharField(max_length=100)
    institution = models.CharField(max_length=100)
    start_year = models.CharField(max_length=4)
    end_year = models.CharField(max_length=4, null=True, blank=True)
    major = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Experience(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='experience')
    company_name = models.CharField(max_length=100)
    total_years_experience = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class JobListing(models.Model):
    """Model for storing job listings scraped from various sources"""
    job_id = models.CharField(max_length=255, unique=True)
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    job_url = models.URLField(max_length=500)
    logo_url = models.URLField(max_length=500, null=True, blank=True)
    source = models.CharField(max_length=50)  # LinkedIn, Indeed, etc.
    posted_date = models.DateField(null=True, blank=True)
    skills = ArrayField(models.CharField(max_length=100), default=list)
    job_type = models.CharField(max_length=100, blank=True)
    seniority_level = models.CharField(max_length=100, blank=True)
    salary_range = models.CharField(max_length=100, blank=True)
    data = models.TextField(blank=True)  # For storing additional JSON data
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['job_id']),
            models.Index(fields=['title']),
            models.Index(fields=['company']),
            models.Index(fields=['location']),
            models.Index(fields=['source']),
            models.Index(fields=['posted_date']),
        ]
        
    def __str__(self):
        return f"{self.title} at {self.company} ({self.source})"