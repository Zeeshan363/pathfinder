from rest_framework import serializers
from ..models import Feedback
from .auth_serializers import UserSerializer

class FeedbackSerializer(serializers.ModelSerializer):
    """Serializer for feedback with user details"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Feedback
        fields = [
            'id', 'user', 'subject', 'message', 'status', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['status', 'created_at', 'updated_at']

class FeedbackCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating feedback"""
    class Meta:
        model = Feedback
        fields = ['subject', 'message']

class FeedbackUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating feedback status (admin only)"""
    class Meta:
        model = Feedback
        fields = ['status'] 