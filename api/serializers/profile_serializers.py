from rest_framework import serializers
from ..models import Profile, Education

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

class CreateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            'about', 'photo_url', 'technical_skills', 'soft_skills',
            'languages', 'interests', 'career_goals'
        ]

class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            'about', 'photo_url', 'technical_skills', 'soft_skills',
            'languages', 'interests', 'career_goals'
        ]

class AddEducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = ['degree', 'institution', 'start_year', 'end_year', 'major']