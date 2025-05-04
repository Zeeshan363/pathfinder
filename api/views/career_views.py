from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
import os
import json
import logging

from ..models import User, Profile
from ..ml.models.career_recommender import CareerRecommender
from ..ml.models.career_chatbot import CareerChatbot

logger = logging.getLogger(__name__)

class CareerViewSet(viewsets.ViewSet):
    """
    API endpoints for career guidance, recommendations, and chatbot interactions.
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize ML models
        try:
            self.career_recommender = CareerRecommender()
            self.career_chatbot = CareerChatbot()
            logger.info("Career ML models initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing career ML models: {e}")
            self.career_recommender = None
            self.career_chatbot = None

    @action(detail=False, methods=['post'])
    def recommend(self, request):
        """
        Get career recommendations based on user skills and interests.
        
        Request body format:
        {
            "skills": ["Python", "Data Analysis", "Machine Learning"],
            "interests": ["Technology", "Research"],  # Optional
            "limit": 5  # Optional, default is 5
        }
        """
        if not self.career_recommender:
            return Response(
                {"error": "Career recommendation model is not available"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        user = request.user
        data = request.data
        skills = data.get('skills', [])
        interests = data.get('interests', [])
        limit = int(data.get('limit', 5))
        
        # If no skills provided, try to get from user profile
        if not skills and hasattr(user, 'profile'):
            try:
                # Get technical skills from user profile
                profile = user.profile
                skills = profile.technical_skills
            except Exception as e:
                logger.error(f"Error getting skills from profile: {e}")
        
        if not skills:
            return Response(
                {"error": "No skills provided or found in profile"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            recommendations = self.career_recommender.get_recommendations(
                user_skills=skills,
                user_interests=interests,
                top_n=limit
            )
            
            return Response({
                "recommendations": recommendations
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Error getting career recommendations: {e}")
            return Response(
                {"error": f"Error processing request: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def skill_gap(self, request):
        """
        Analyze skill gaps for a specific career path.
        
        Request body format:
        {
            "career_title": "Data Scientist",
            "skills": ["Python", "Statistics"]  # Optional, will use profile if not provided
        }
        """
        if not self.career_recommender:
            return Response(
                {"error": "Career recommendation model is not available"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        user = request.user
        data = request.data
        career_title = data.get('career_title')
        skills = data.get('skills', [])
        
        if not career_title:
            return Response(
                {"error": "Career title is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # If no skills provided, try to get from user profile
        if not skills and hasattr(user, 'profile'):
            try:
                profile = user.profile
                skills = profile.technical_skills
            except Exception as e:
                logger.error(f"Error getting skills from profile: {e}")
        
        if not skills:
            return Response(
                {"error": "No skills provided or found in profile"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            skill_gap = self.career_recommender.get_skill_gaps(
                user_skills=skills,
                career_title=career_title
            )
            
            if 'error' in skill_gap:
                return Response(
                    {"error": skill_gap['error']},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response(skill_gap, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Error analyzing skill gap: {e}")
            return Response(
                {"error": f"Error processing request: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def chatbot(self, request):
        """
        Interact with the career guidance chatbot.
        
        Request body format:
        {
            "message": "What career should I pursue?",
            "context": {...},  # Optional, conversation context
            "use_profile": true  # Optional, whether to use profile skills/interests
        }
        """
        if not self.career_chatbot:
            return Response(
                {"error": "Career chatbot is not available"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        user = request.user
        data = request.data
        message = data.get('message')
        context = data.get('context')
        use_profile = data.get('use_profile', True)
        
        if not message:
            return Response(
                {"error": "Message is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        skills = []
        interests = []
        
        # If use_profile is True, get skills and interests from user profile
        if use_profile and hasattr(user, 'profile'):
            try:
                profile = user.profile
                skills = profile.technical_skills
                interests = profile.interests
            except Exception as e:
                logger.error(f"Error getting profile data: {e}")
        
        try:
            response = self.career_chatbot.process_message(
                message=message,
                user_skills=skills,
                user_interests=interests,
                user_context=context
            )
            
            return Response(response, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Error processing chatbot message: {e}")
            return Response(
                {"error": f"Error processing request: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def train_chatbot(self, request):
        """
        Add new training data to the chatbot.
        
        Request body format:
        {
            "message": "What skills do I need for a blockchain developer?",
            "intent": "skill_gap",
            "response": "For a blockchain developer, you typically need skills in..."
        }
        
        Or to create a new intent:
        {
            "new_intent": "job_search",
            "patterns": ["How do I find jobs?", "Where to apply for jobs"],
            "responses": ["You can find jobs on LinkedIn and other job boards"]
        }
        """
        if not self.career_chatbot:
            return Response(
                {"error": "Career chatbot is not available"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        if not request.user.is_staff:
            return Response(
                {"error": "Only staff users can train the chatbot"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        data = request.data
        
        # Check if we're creating a new intent
        if data.get('new_intent'):
            new_intent = data.get('new_intent')
            patterns = data.get('patterns', [])
            responses = data.get('responses', [])
            
            if not patterns or not responses:
                return Response(
                    {"error": "Patterns and responses are required for new intents"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            result = self.career_chatbot.create_new_intent(
                tag=new_intent,
                patterns=patterns,
                responses=responses
            )
            
            if result:
                # Retrain the model
                self.career_chatbot.retrain_model()
                return Response(
                    {"success": f"Created new intent: {new_intent}"},
                    status=status.HTTP_201_CREATED
                )
            else:
                return Response(
                    {"error": f"Intent '{new_intent}' already exists or is invalid"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Otherwise, add an example to an existing intent
        message = data.get('message')
        intent = data.get('intent')
        response = data.get('response')
        
        if not message or not intent:
            return Response(
                {"error": "Message and intent are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        result = self.career_chatbot.add_training_example(
            message=message,
            intent_tag=intent,
            response=response
        )
        
        if result:
            # Retrain the model after adding a new example
            self.career_chatbot.retrain_model()
            return Response(
                {"success": f"Added training example to intent: {intent}"},
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                {"error": f"Intent '{intent}' not found or message is invalid"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def careers(self, request):
        """
        Get available career paths for reference.
        """
        if not self.career_recommender:
            return Response(
                {"error": "Career recommendation model is not available"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        try:
            careers = self.career_recommender.career_paths
            return Response({
                "careers": careers
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Error getting career paths: {e}")
            return Response(
                {"error": f"Error processing request: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def train_model(self, request):
        """
        Train or retrain the career recommendation model with new data.
        Restricted to staff users only.
        
        Request body format:
        {
            "epochs": 100,  # Optional
            "learning_rate": 0.001  # Optional
        }
        """
        if not request.user.is_staff:
            return Response(
                {"error": "Only staff users can train models"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not self.career_recommender:
            return Response(
                {"error": "Career recommendation model is not available"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        data = request.data
        epochs = data.get('epochs', 100)
        learning_rate = data.get('learning_rate', 0.001)
        
        try:
            result = self.career_recommender.train_model(
                epochs=epochs,
                learning_rate=learning_rate
            )
            
            return Response({
                "success": True,
                "message": "Model training completed",
                "result": result
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Error training career model: {e}")
            return Response(
                {"error": f"Error training model: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 