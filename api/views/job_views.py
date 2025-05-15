from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
import logging
from ..models import JobListing, Profile
from ..serializers.job_serializers import (
    JobListingSerializer, JobListingSummarySerializer, RelevantJobListingSerializer
)
from ..services.job_scraper_service import LinkedInJobScraper
from api.ml.models.job_recommender import JobRecommender

logger = logging.getLogger(__name__)

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class JobListingsView(APIView):
    """View for listing and filtering job listings"""
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get(self, request):
        try:
            # Get query parameters for filtering
            search_query = request.query_params.get('search', '')
            location = request.query_params.get('location', '')
            job_type = request.query_params.get('job_type', '')
            source = request.query_params.get('source', '')
            skill = request.query_params.get('skill', '')
            
            # Base queryset with active jobs only
            queryset = JobListing.objects.filter(is_active=True)
            
            # Apply filters if provided
            if search_query:
                queryset = queryset.filter(
                    Q(title__icontains=search_query) | 
                    Q(company__icontains=search_query) |
                    Q(description__icontains=search_query)
                )
            
            if location:
                queryset = queryset.filter(location__icontains=location)
                
            if job_type:
                queryset = queryset.filter(job_type__icontains=job_type)
                
            if source:
                queryset = queryset.filter(source=source)
                
            if skill:
                queryset = queryset.filter(skills__contains=[skill])
            
            # Order by most recent
            queryset = queryset.order_by('-posted_date', '-created_at')
            
            # Apply pagination
            paginator = self.pagination_class()
            page = paginator.paginate_queryset(queryset, request)
            
            if page is not None:
                serializer = JobListingSummarySerializer(page, many=True)
                return paginator.get_paginated_response(serializer.data)
            
            serializer = JobListingSummarySerializer(queryset, many=True)
            return Response(serializer.data)
        
        except Exception as e:
            logger.error(f"Error retrieving job listings: {str(e)}")
            return Response(
                {"error": "Failed to retrieve job listings"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class JobDetailView(APIView):
    """View for retrieving detailed job information"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, job_id):
        try:
            job = JobListing.objects.get(pk=job_id)
            serializer = JobListingSerializer(job)
            return Response(serializer.data)
        except JobListing.DoesNotExist:
            return Response(
                {"error": "Job listing not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error retrieving job detail: {str(e)}")
            return Response(
                {"error": "Failed to retrieve job detail"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class RelevantJobsView(APIView):
    """View for retrieving job listings relevant to the user's profile"""
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get(self, request):
        try:
            # Get user profile
            try:
                profile = request.user.profile
            except Profile.DoesNotExist:
                return Response(
                    {"error": "Profile not found. Please complete your profile first."},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get user skills from profile
            user_skills = profile.technical_skills
            
            if not user_skills:
                return Response(
                    {"error": "No skills found in your profile. Please add skills to get relevant job recommendations."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get all active job listings
            job_listings = JobListing.objects.filter(is_active=True)
            
            # Calculate relevance score for each job
            relevant_jobs = []
            
            for job in job_listings:
                # Check for skill match
                matching_skills = []
                
                # Compare user skills with job skills
                for skill in user_skills:
                    # Check if skill is in job title
                    if skill.lower() in job.title.lower():
                        matching_skills.append(skill)
                        
                    # Check if skill is in job description
                    if skill.lower() in job.description.lower():
                        if skill not in matching_skills:
                            matching_skills.append(skill)
                            
                    # Check if skill is in job skills list
                    if skill in job.skills:
                        if skill not in matching_skills:
                            matching_skills.append(skill)
                
                # Calculate relevance score (simple percentage of matching skills)
                score = len(matching_skills) / len(user_skills) if user_skills else 0
                
                # Only include jobs with at least one matching skill
                if matching_skills:
                    job_data = {
                        'job': job,
                        'relevance_score': score,
                        'matching_skills': matching_skills
                    }
                    relevant_jobs.append(job_data)
            
            # Sort by relevance score (descending)
            relevant_jobs.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            # Apply pagination
            paginator = self.pagination_class()
            page = paginator.paginate_queryset(relevant_jobs, request)
            
            if page is not None:
                # Create serialized response with relevance info
                result = []
                for item in page:
                    job_serializer = RelevantJobListingSerializer(item['job'])
                    job_data = job_serializer.data
                    job_data['relevance_score'] = item['relevance_score']
                    job_data['matching_skills'] = item['matching_skills']
                    result.append(job_data)
                
                return paginator.get_paginated_response(result)
            
            # If no pagination
            result = []
            for item in relevant_jobs:
                job_serializer = RelevantJobListingSerializer(item['job'])
                job_data = job_serializer.data
                job_data['relevance_score'] = item['relevance_score']
                job_data['matching_skills'] = item['matching_skills']
                result.append(job_data)
                
            return Response(result)
            
        except Exception as e:
            logger.error(f"Error retrieving relevant jobs: {str(e)}")
            return Response(
                {"error": "Failed to retrieve relevant jobs"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ScrapeJobsView(APIView):
    """View for triggering job scraping"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Get parameters from request
            keywords = request.data.get('keywords', '')
            location = request.data.get('location', '')
            limit = int(request.data.get('limit', 25))
            
            if not keywords:
                return Response(
                    {"error": "Keywords parameter is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Initialize the scraper
            scraper = LinkedInJobScraper()
            
            # Scrape jobs
            job_listings = scraper.search_jobs(
                keywords=keywords,
                location=location,
                results_limit=limit
            )
            
            # Store jobs in database
            jobs_stored = scraper.store_job_listings(job_listings)
            
            return Response({
                "message": f"Successfully scraped and stored {jobs_stored} job listings",
                "jobs_found": len(job_listings),
                "jobs_stored": jobs_stored
            })
            
        except Exception as e:
            logger.error(f"Error scraping jobs: {str(e)}")
            return Response(
                {"error": f"Failed to scrape jobs: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class JobRecommendationView(APIView):
    """AI-powered job recommendations for the user"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            profile = request.user.profile
        except Profile.DoesNotExist:
            return Response({"error": "Profile not found. Please complete your profile first."}, status=status.HTTP_404_NOT_FOUND)
        recommender = JobRecommender()
        recommendations = recommender.get_recommendations(profile, top_n=10)
        # Serialize jobs and add match info
        result = []
        for rec in recommendations:
            job = rec['job']
            result.append({
                'id': job.id,
                'title': job.title,
                'company': job.company,
                'location': job.location,
                'description': job.description,
                'job_url': job.job_url,
                'logo_url': job.logo_url,
                'source': job.source,
                'posted_date': job.posted_date,
                'skills': job.skills,
                'job_type': job.job_type,
                'seniority_level': job.seniority_level,
                'salary_range': job.salary_range,
                'match_score': rec['match_score'],
                'matching_skills': rec['matching_skills'],
                'missing_skills': rec['missing_skills'],
            })
        return Response({'recommendations': result}, status=status.HTTP_200_OK) 