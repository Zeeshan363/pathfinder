from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from ..services.recommendation_service import RecommendationService

class GetCareerPathsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            recommendation_service = RecommendationService()
            recommendations = recommendation_service.get_career_path_recommendations(request.user.id)
            # Convert recommendation objects to dictionaries
            recommendation_dicts = [recommendation.to_dict() for recommendation in recommendations]
            return Response(recommendation_dicts, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() else status.HTTP_500_INTERNAL_SERVER_ERROR
            )