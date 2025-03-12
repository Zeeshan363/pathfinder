from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = 'STUDENT', 'Student'
        PROFESSIONAL = 'PROFESSIONAL', 'Professional'
        COUNSELOR = 'COUNSELOR', 'Counselor'
        ADMIN = 'ADMIN', 'Admin'
    
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