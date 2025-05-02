from django.contrib import admin
from .models import User, Profile, Education, Experience, JobListing

class EducationInline(admin.TabularInline):
    model = Education
    extra = 1

class ExperienceInline(admin.TabularInline):
    model = Experience
    extra = 1

class ProfileAdmin(admin.ModelAdmin):
    inlines = [EducationInline, ExperienceInline]
    list_display = ('id', 'user', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email')

class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'role', 'is_verified', 'is_profile_complete')
    list_filter = ('role', 'is_verified', 'is_profile_complete')
    search_fields = ('username', 'email')

class JobListingAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'company', 'location', 'source', 'posted_date', 'created_at')
    list_filter = ('source', 'posted_date', 'job_type', 'seniority_level', 'is_active')
    search_fields = ('title', 'company', 'description', 'location')
    readonly_fields = ('job_id', 'created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('job_id', 'title', 'company', 'location', 'job_url', 'logo_url', 'is_active')
        }),
        ('Details', {
            'fields': ('description', 'skills', 'job_type', 'seniority_level', 'salary_range')
        }),
        ('Metadata', {
            'fields': ('source', 'posted_date', 'data', 'created_at', 'updated_at')
        }),
    )

admin.site.register(User, UserAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(Education)
admin.site.register(Experience)
admin.site.register(JobListing, JobListingAdmin)