from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views.auth_views import RegisterView, CustomTokenObtainPairView, GetAllUsersView
from .views.profile_views import (
    CreateProfileView, GetProfileByJWTView, UpdateProfileView, 
    AddEducationToProfileView, DeleteEducationFromProfileView,
    AddExperienceToProfileView, DeleteExperienceFromProfileView
)
from .views.recommendation_views import GetCareerPathsView

urlpatterns = [
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
]