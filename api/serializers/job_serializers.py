from rest_framework import serializers
from ..models import JobListing

class JobListingSerializer(serializers.ModelSerializer):
    """Serializer for job listings with all fields"""
    class Meta:
        model = JobListing
        fields = [
            'id', 'job_id', 'title', 'company', 'location', 'description',
            'job_url', 'logo_url', 'source', 'posted_date', 'skills',
            'job_type', 'seniority_level', 'salary_range', 'is_active',
            'created_at', 'updated_at'
        ]

class JobListingSummarySerializer(serializers.ModelSerializer):
    """Serializer for job listings with summary information"""
    class Meta:
        model = JobListing
        fields = [
            'id', 'job_id', 'title', 'company', 'location',
            'logo_url', 'source', 'posted_date', 'job_type',
            'seniority_level', 'salary_range'
        ]
        
class RelevantJobListingSerializer(serializers.ModelSerializer):
    """Serializer for job listings with relevance score"""
    relevance_score = serializers.FloatField(read_only=True)
    matching_skills = serializers.ListField(child=serializers.CharField(), read_only=True)
    
    class Meta:
        model = JobListing
        fields = [
            'id', 'job_id', 'title', 'company', 'location',
            'job_url', 'logo_url', 'source', 'posted_date',
            'skills', 'job_type', 'seniority_level',
            'relevance_score', 'matching_skills'
        ] 