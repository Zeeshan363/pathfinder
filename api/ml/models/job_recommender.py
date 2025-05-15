import torch
import torch.nn as nn
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from api.models import JobListing, Profile

class JobEmbeddingModel(nn.Module):
    def __init__(self, input_size, hidden_size, output_size):
        super(JobEmbeddingModel, self).__init__()
        self.embedding_layer = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, output_size)
        )
    def forward(self, x):
        return self.embedding_layer(x)

class JobRecommender:
    def __init__(self, model_path=None):
        self.input_size = 100
        self.hidden_size = 50
        self.output_size = 20
        self.model = JobEmbeddingModel(self.input_size, self.hidden_size, self.output_size)
        self.vectorizer = TfidfVectorizer(max_features=self.input_size)
        self.model_path = model_path or 'job_model.pth'
        # Try to load pre-trained model if it exists
        try:
            self.model.load_state_dict(torch.load(self.model_path))
            self.model.eval()
        except Exception:
            pass

    def get_recommendations(self, user_profile: Profile, top_n=5):
        # Gather all jobs from the database
        jobs = list(JobListing.objects.filter(is_active=True))
        if not jobs:
            # TODO: Trigger LinkedIn scrape here if needed
            return []
        # Prepare job skills for vectorizer
        job_skills_texts = [' '.join(job.skills) for job in jobs]
        self.vectorizer.fit(job_skills_texts)
        job_vectors = self.vectorizer.transform(job_skills_texts).toarray()
        # Prepare user skills
        user_skills = (user_profile.technical_skills or []) + (user_profile.soft_skills or [])
        user_skills_text = ' '.join(user_skills)
        user_vector = self.vectorizer.transform([user_skills_text]).toarray()
        # Use cosine similarity for now (can be replaced with model embeddings)
        similarities = cosine_similarity(user_vector, job_vectors).flatten()
        # Get top N jobs
        top_indices = similarities.argsort()[-top_n:][::-1]
        recommendations = []
        for idx in top_indices:
            job = jobs[idx]
            score = float(similarities[idx])
            matching_skills = [skill for skill in user_skills if skill in job.skills]
            missing_skills = [skill for skill in job.skills if skill not in user_skills]
            recommendations.append({
                'job': job,
                'match_score': round(score, 2),
                'matching_skills': matching_skills,
                'missing_skills': missing_skills
            })
        return recommendations 