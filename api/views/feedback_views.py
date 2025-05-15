from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from ..models import Feedback
from ..permissions import IsAdminRole
from ..serializers.feedback_serializers import (
    FeedbackSerializer, 
    FeedbackCreateSerializer,
    FeedbackUpdateSerializer
)
import logging

logger = logging.getLogger(__name__)

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class FeedbackListView(APIView):
    """View for listing all feedback (admin only)"""
    permission_classes = [IsAuthenticated, IsAdminRole]
    pagination_class = StandardResultsSetPagination
    
    def get(self, request):
        try:
            # Get all feedback, ordered by most recent first
            feedback = Feedback.objects.all()
            
            # Apply pagination
            paginator = self.pagination_class()
            page = paginator.paginate_queryset(feedback, request)
            
            if page is not None:
                serializer = FeedbackSerializer(page, many=True)
                return paginator.get_paginated_response(serializer.data)
            
            serializer = FeedbackSerializer(feedback, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error retrieving feedback: {str(e)}")
            return Response(
                {"error": "Failed to retrieve feedback"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class UserFeedbackListView(APIView):
    """View for listing a user's own feedback"""
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get(self, request):
        try:
            # Get user's feedback, ordered by most recent first
            feedback = Feedback.objects.filter(user=request.user)
            
            # Apply pagination
            paginator = self.pagination_class()
            page = paginator.paginate_queryset(feedback, request)
            
            if page is not None:
                serializer = FeedbackSerializer(page, many=True)
                return paginator.get_paginated_response(serializer.data)
            
            serializer = FeedbackSerializer(feedback, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error retrieving user feedback: {str(e)}")
            return Response(
                {"error": "Failed to retrieve feedback"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CreateFeedbackView(APIView):
    """View for creating new feedback"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            serializer = FeedbackCreateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Create feedback with current user
            feedback = Feedback.objects.create(
                user=request.user,
                subject=serializer.validated_data['subject'],
                message=serializer.validated_data['message']
            )
            
            return Response(
                FeedbackSerializer(feedback).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            logger.error(f"Error creating feedback: {str(e)}")
            return Response(
                {"error": "Failed to create feedback"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class UpdateFeedbackStatusView(APIView):
    """View for updating feedback status (admin only)"""
    permission_classes = [IsAuthenticated, IsAdminRole]
    
    def put(self, request, feedback_id):
        try:
            feedback = get_object_or_404(Feedback, pk=feedback_id)
            serializer = FeedbackUpdateSerializer(feedback, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            
            return Response(
                FeedbackSerializer(feedback).data,
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error updating feedback status: {str(e)}")
            return Response(
                {"error": "Failed to update feedback status"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 