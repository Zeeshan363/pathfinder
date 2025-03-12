from django.urls import path
from .views import CareerRecommendationView

urlpatterns = [
    path('recommendations/', CareerRecommendationView.as_view(), name='career-recommendations'),
    path('recommendations/<int:user_id>/', CareerRecommendationView.as_view(), name='career-recommendations-for-user'),
]