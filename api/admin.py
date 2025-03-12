from django.contrib import admin
from .models import User, Profile, Education

class EducationInline(admin.TabularInline):
    model = Education
    extra = 1

class ProfileAdmin(admin.ModelAdmin):
    inlines = [EducationInline]
    list_display = ('id', 'user', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email')

class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'role', 'is_verified', 'is_profile_complete')
    list_filter = ('role', 'is_verified', 'is_profile_complete')
    search_fields = ('username', 'email')

admin.site.register(User, UserAdmin)
admin.site.register(Profile, ProfileAdmin)