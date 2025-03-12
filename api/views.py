from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .serializers import CareerPathSerializer
from .services.recommendation_service import RecommendationService

class CareerRecommendationView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, user_id=None):
        recommendation_service = RecommendationService()
        
        # If user_id is not provided, use the authenticated user's ID
        if user_id is None:
            user_id = request.user.id
        
        try:
            recommendations = recommendation_service.get_career_path_recommendations(user_id)
            # Convert recommendation objects to dictionaries
            recommendation_dicts = [recommendation.to_dict() for recommendation in recommendations]
            # Serialize the data
            serializer = CareerPathSerializer(recommendation_dicts, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() else status.HTTP_500_INTERNAL_SERVER_ERROR
            )