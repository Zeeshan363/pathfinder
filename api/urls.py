from django.urls import path, include
from rest_framework import routers
from rest_framework_simplejwt.views import TokenRefreshView
from .views.auth_views import RegisterView, CustomTokenObtainPairView, GetAllUsersView
from .views.profile_views import (
    CreateProfileView, GetProfileByJWTView, UpdateProfileView, 
    AddEducationToProfileView, DeleteEducationFromProfileView,
    AddExperienceToProfileView, DeleteExperienceFromProfileView
)
from .views.recommendation_views import GetCareerPathsView
from .views.job_views import (
    JobListingsView, JobDetailView, RelevantJobsView, ScrapeJobsView, JobRecommendationView
)
from .views.career_views import CareerViewSet
from .views.feedback_views import (
    FeedbackListView, UserFeedbackListView, CreateFeedbackView, UpdateFeedbackStatusView
)

router = routers.DefaultRouter()
router.register(r'career', CareerViewSet, basename='career')

urlpatterns = [
    path('', include(router.urls)),
    
    # Auth routes
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/getAllUsers/', GetAllUsersView.as_view(), name='get-all-users'),
    
    # Profile routes
    path('profile/createProfile/', CreateProfileView.as_view(), name='create-profile'),
    path('profile/getProfileByJWT/', GetProfileByJWTView.as_view(), name='get-profile-by-jwt'),
    path('profile/updateProfile/', UpdateProfileView.as_view(), name='update-profile'),
    path('profile/addEducationToProfile/', AddEducationToProfileView.as_view(), name='add-education'),
    path('profile/deleteEducationFromProfile/<int:education_id>/', DeleteEducationFromProfileView.as_view(), name='delete-education'),
    path('profile/addExperienceToProfile/', AddExperienceToProfileView.as_view(), name='add-experience'),
    path('profile/deleteExperienceFromProfile/<int:experience_id>/', DeleteExperienceFromProfileView.as_view(), name='delete-experience'),
    
    # Recommendation routes
    path('recommendation/getCareerPaths/', GetCareerPathsView.as_view(), name='get-career-paths'),
    
    # Job routes
    path('jobs/', JobListingsView.as_view(), name='job-listings'),
    path('jobs/<int:job_id>/', JobDetailView.as_view(), name='job-detail'),
    path('jobs/relevant/', RelevantJobsView.as_view(), name='relevant-jobs'),
    path('jobs/scrape/', ScrapeJobsView.as_view(), name='scrape-jobs'),
    path('jobs/recommend/', JobRecommendationView.as_view(), name='job-recommend'),
    
    # Feedback routes
    path('feedback/', FeedbackListView.as_view(), name='feedback-list'),
    path('feedback/user/', UserFeedbackListView.as_view(), name='user-feedback'),
    path('feedback/create/', CreateFeedbackView.as_view(), name='create-feedback'),
    path('feedback/update/<int:feedback_id>/', UpdateFeedbackStatusView.as_view(), name='update-feedback'),
]