from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from ..models import Profile, Education, Experience
from ..serializers.profile_serializers import (
    ProfileSerializer, CreateProfileSerializer, UpdateProfileSerializer,
    AddEducationSerializer, EducationSerializer,
    AddExperienceSerializer, ExperienceSerializer
)

class CreateProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Check if profile already exists
        if hasattr(request.user, 'profile'):
            return Response(
                {"error": "Profile already exists for this user"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = CreateProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile = serializer.save(user=request.user)
        
        # Update user's profile_complete status
        request.user.is_profile_complete = True
        request.user.save()
        
        return Response(ProfileSerializer(profile).data, status=status.HTTP_201_CREATED)

class GetProfileByJWTView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            profile = request.user.profile
            serializer = ProfileSerializer(profile)
            return Response(serializer.data)
        except Profile.DoesNotExist:
            return Response(
                {"error": "Profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

class UpdateProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    def put(self, request):
        try:
            profile = request.user.profile
            serializer = UpdateProfileSerializer(profile, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(ProfileSerializer(profile).data)
        except Profile.DoesNotExist:
            return Response(
                {"error": "Profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

class AddEducationToProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            profile = request.user.profile
            serializer = AddEducationSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            education = serializer.save(profile=profile)
            return Response(EducationSerializer(education).data, status=status.HTTP_201_CREATED)
        except Profile.DoesNotExist:
            return Response(
                {"error": "Profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

class DeleteEducationFromProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, education_id):
        try:
            profile = request.user.profile
            education = get_object_or_404(Education, id=education_id, profile=profile)
            education.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Profile.DoesNotExist:
            return Response(
                {"error": "Profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

class AddExperienceToProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            profile = request.user.profile
            serializer = AddExperienceSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            experience = serializer.save(profile=profile)
            return Response(ExperienceSerializer(experience).data, status=status.HTTP_201_CREATED)
        except Profile.DoesNotExist:
            return Response(
                {"error": "Profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

class DeleteExperienceFromProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, experience_id):
        try:
            profile = request.user.profile
            experience = get_object_or_404(Experience, id=experience_id, profile=profile)
            experience.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Profile.DoesNotExist:
            return Response(
                {"error": "Profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )