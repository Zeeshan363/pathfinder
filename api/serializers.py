from rest_framework import serializers
from .models import User, Profile, Education

class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = ['id', 'degree', 'institution', 'start_year', 'end_year', 'major']

class ProfileSerializer(serializers.ModelSerializer):
    education = EducationSerializer(many=True, read_only=True)
    
    class Meta:
        model = Profile
        fields = [
            'id', 'about', 'photo_url', 'technical_skills', 'soft_skills',
            'languages', 'interests', 'career_goals', 'education'
        ]

class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'name', 'role', 'is_verified', 'is_profile_complete', 'profile']
        read_only_fields = ['is_verified', 'is_profile_complete']

class CareerPathSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    description = serializers.CharField()
    requiredSkills = serializers.ListField(child=serializers.CharField())
    relatedInterests = serializers.ListField(child=serializers.CharField())
    matchScore = serializers.FloatField()