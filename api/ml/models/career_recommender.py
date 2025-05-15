try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
import numpy as np
import os
import json
import logging
from collections import defaultdict
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

logger = logging.getLogger(__name__)

if TORCH_AVAILABLE:
    class CareerEmbeddingModel(nn.Module):
        """
        Neural network model for embedding skills and career paths into a shared vector space
        """
        def __init__(self, input_size, hidden_size, output_size):
            super(CareerEmbeddingModel, self).__init__()
            self.embedding_layer = nn.Sequential(
                nn.Linear(input_size, hidden_size),
                nn.ReLU(),
                nn.Linear(hidden_size, output_size)
            )
            
        def forward(self, x):
            return self.embedding_layer(x)
else:
    # Fallback placeholder class when torch is not available
    class CareerEmbeddingModel:
        def __init__(self, input_size, hidden_size, output_size):
            self.input_size = input_size
            self.hidden_size = hidden_size
            self.output_size = output_size

class CareerRecommender:
    """
    Career recommendation system using skill-based matching and PyTorch embeddings
    """
    def __init__(self, model_path=None, career_data_path=None):
        # Model parameters
        self.input_size = 100  # Size of skill vector (TF-IDF)
        self.hidden_size = 50
        self.output_size = 20  # Size of embedding vector
        
        # Initialize model
        self.model = CareerEmbeddingModel(self.input_size, self.hidden_size, self.output_size)
        
        # Directory paths
        module_dir = os.path.dirname(os.path.abspath(__file__))
        self.model_path = model_path or os.path.join(module_dir, '../../ml/data/career_model.pth')
        self.career_data_path = career_data_path or os.path.join(module_dir, '../../ml/data/career_paths.json')
        
        # Load career paths data and vectorizer
        self.career_paths = self._load_career_paths()
        if SKLEARN_AVAILABLE:
            self.vectorizer = TfidfVectorizer(max_features=self.input_size)
            self.skill_matrix = None
            
            # If skills data exists, fit the vectorizer
            if self.career_paths:
                # Extract all skills from career paths for vectorizer training
                all_skills = []
                for career in self.career_paths:
                    skills_text = ' '.join(career.get('required_skills', []))
                    all_skills.append(skills_text)
                
                # Fit vectorizer on all skills
                if all_skills:
                    self.skill_matrix = self.vectorizer.fit_transform(all_skills)
        
        # Try to load pre-trained model if it exists
        if TORCH_AVAILABLE:
            try:
                if os.path.exists(self.model_path):
                    self.model.load_state_dict(torch.load(self.model_path))
                    self.model.eval()
                    logger.info(f"Loaded pre-trained career model from {self.model_path}")
            except Exception as e:
                logger.warning(f"Could not load pre-trained model: {str(e)}")
    
    def _load_career_paths(self):
        """Load career paths data from JSON file"""
        try:
            if os.path.exists(self.career_data_path):
                with open(self.career_data_path, 'r') as f:
                    return json.load(f)
            else:
                # Return sample data if file doesn't exist
                logger.warning(f"Career paths data file not found at {self.career_data_path}, using sample data.")
                return self._get_sample_career_data()
        except Exception as e:
            logger.error(f"Error loading career paths data: {str(e)}")
            return self._get_sample_career_data()
    
    def _get_sample_career_data(self):
        """Return sample career paths data for demonstration"""
        return [
            {
                "id": 1,
                "title": "Data Scientist",
                "description": "Analyze and interpret complex data to make business decisions",
                "required_skills": ["Python", "SQL", "Machine Learning", "Statistics", "Data Visualization", "Deep Learning", "R", "TensorFlow", "PyTorch", "Big Data"],
                "education": ["Master's in Computer Science", "PhD in Statistics"],
                "salary_range": "$90,000 - $150,000",
                "growth_potential": "High",
                "industry": "Technology"
            },
            {
                "id": 2,
                "title": "Software Engineer",
                "description": "Design and build applications and systems",
                "required_skills": ["Java", "Python", "JavaScript", "Object-Oriented Programming", "Algorithms", "Data Structures", "Git", "Agile", "REST APIs", "SQL"],
                "education": ["Bachelor's in Computer Science", "Bachelor's in Software Engineering"],
                "salary_range": "$80,000 - $140,000",
                "growth_potential": "High",
                "industry": "Technology"
            },
            {
                "id": 3,
                "title": "UX/UI Designer",
                "description": "Create user-friendly interfaces and experiences",
                "required_skills": ["Wireframing", "Prototyping", "User Research", "Adobe XD", "Figma", "Sketch", "HTML", "CSS", "JavaScript", "Design Thinking"],
                "education": ["Bachelor's in Design", "Bachelor's in Human-Computer Interaction"],
                "salary_range": "$70,000 - $120,000",
                "growth_potential": "Medium",
                "industry": "Design"
            },
            {
                "id": 4,
                "title": "Product Manager",
                "description": "Define product vision and strategy to deliver successful products",
                "required_skills": ["Product Strategy", "Market Research", "User Stories", "Agile", "Roadmapping", "Stakeholder Management", "Analytics", "A/B Testing", "Presentation", "Leadership"],
                "education": ["Bachelor's in Business", "MBA", "Bachelor's in Computer Science"],
                "salary_range": "$90,000 - $160,000",
                "growth_potential": "High",
                "industry": "Technology"
            },
            {
                "id": 5,
                "title": "DevOps Engineer",
                "description": "Implement automation and streamline development operations",
                "required_skills": ["Linux", "Docker", "Kubernetes", "AWS", "CI/CD", "Python", "Bash", "Infrastructure as Code", "Monitoring", "Cloud Architecture"],
                "education": ["Bachelor's in Computer Science", "Bachelor's in Information Technology"],
                "salary_range": "$85,000 - $140,000",
                "growth_potential": "High",
                "industry": "Technology"
            },
            {
                "id": 6,
                "title": "Data Analyst",
                "description": "Analyze data to help companies make better business decisions",
                "required_skills": ["SQL", "Excel", "Data Visualization", "Python", "R", "Tableau", "Power BI", "Statistics", "ETL", "Reporting"],
                "education": ["Bachelor's in Statistics", "Bachelor's in Economics", "Bachelor's in Computer Science"],
                "salary_range": "$60,000 - $100,000",
                "growth_potential": "Medium",
                "industry": "Business Intelligence"
            },
            {
                "id": 7,
                "title": "Machine Learning Engineer",
                "description": "Build and deploy machine learning models into production",
                "required_skills": ["Python", "TensorFlow", "PyTorch", "Machine Learning", "Deep Learning", "Computer Vision", "NLP", "MLOps", "Docker", "Cloud Platforms"],
                "education": ["Master's in Computer Science", "PhD in Machine Learning"],
                "salary_range": "$100,000 - $170,000",
                "growth_potential": "Very High",
                "industry": "Artificial Intelligence"
            },
            {
                "id": 8,
                "title": "Frontend Developer",
                "description": "Create responsive and interactive web applications",
                "required_skills": ["HTML", "CSS", "JavaScript", "React", "Angular", "Vue.js", "Redux", "Responsive Design", "Webpack", "UI Frameworks"],
                "education": ["Bachelor's in Computer Science", "Web Development Bootcamp"],
                "salary_range": "$70,000 - $130,000",
                "growth_potential": "Medium",
                "industry": "Web Development"
            },
            {
                "id": 9,
                "title": "Backend Developer",
                "description": "Build server-side logic and integrate with databases and services",
                "required_skills": ["Python", "Java", "Node.js", "Databases", "REST APIs", "GraphQL", "Microservices", "Authentication", "Cloud Services", "Security"],
                "education": ["Bachelor's in Computer Science", "Backend Development Bootcamp"],
                "salary_range": "$80,000 - $140,000",
                "growth_potential": "Medium",
                "industry": "Web Development"
            },
            {
                "id": 10,
                "title": "Cybersecurity Analyst",
                "description": "Protect systems and data from cyber threats",
                "required_skills": ["Network Security", "Penetration Testing", "Security Audits", "Incident Response", "Ethical Hacking", "Cryptography", "Risk Assessment", "Security Tools", "Compliance", "Threat Intelligence"],
                "education": ["Bachelor's in Cybersecurity", "Bachelor's in Computer Science"],
                "salary_range": "$80,000 - $140,000",
                "growth_potential": "High",
                "industry": "Security"
            }
        ]
    
    def save_model(self):
        """Save the trained model to disk"""
        if not TORCH_AVAILABLE:
            logger.error("PyTorch not available, cannot save model")
            return False
            
        try:
            model_dir = os.path.dirname(self.model_path)
            if not os.path.exists(model_dir):
                os.makedirs(model_dir)
            torch.save(self.model.state_dict(), self.model_path)
            logger.info(f"Model saved to {self.model_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
            return False
    
    def save_career_paths(self, career_paths):
        """Save career paths data to JSON file"""
        try:
            data_dir = os.path.dirname(self.career_data_path)
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
            with open(self.career_data_path, 'w') as f:
                json.dump(career_paths, f, indent=2)
            logger.info(f"Career paths data saved to {self.career_data_path}")
            self.career_paths = career_paths
            return True
        except Exception as e:
            logger.error(f"Error saving career paths data: {str(e)}")
            return False
    
    def train(self, epochs=100, learning_rate=0.001):
        """Train the career recommendation model"""
        if not TORCH_AVAILABLE or not SKLEARN_AVAILABLE:
            logger.error("PyTorch or scikit-learn not available, cannot train model")
            return False
            
        if not self.career_paths or len(self.career_paths) < 2:
            logger.error("Not enough career paths data for training")
            return False
        
        # Extract skills for training
        all_skills = []
        for career in self.career_paths:
            skills_text = ' '.join(career.get('required_skills', []))
            all_skills.append(skills_text)
        
        # Prepare skill vectors
        self.skill_matrix = self.vectorizer.fit_transform(all_skills)
        skill_vectors = torch.FloatTensor(self.skill_matrix.toarray())
        
        # Define loss function and optimizer
        criterion = nn.MSELoss()
        optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)
        
        # Train the model
        self.model.train()
        for epoch in range(epochs):
            optimizer.zero_grad()
            outputs = self.model(skill_vectors)
            
            # Use contrastive loss - skills for similar careers should be closer
            loss = criterion(outputs, skill_vectors)
            
            loss.backward()
            optimizer.step()
            
        return True
    
    def get_recommendations(self, user_skills, user_interests=None, top_n=5):
        """
        Get career recommendations based on user skills and interests
        
        Args:
            user_skills (list): List of user's skills
            user_interests (list, optional): List of user's interests
            top_n (int): Number of recommendations to return
            
        Returns:
            list: List of recommended careers with scores
        """
        if not self.career_paths:
            logger.error("No career paths data available")
            return []
            
        if not SKLEARN_AVAILABLE:
            # Fallback to simple matching if sklearn is not available
            recommendations = []
            for career in self.career_paths:
                required_skills = career.get('required_skills', [])
                matching_skills = [skill for skill in user_skills if skill in required_skills]
                score = len(matching_skills) / max(len(required_skills), 1) if required_skills else 0
                
                recommendations.append({
                    'career': career,
                    'score': score,
                    'matching_skills': matching_skills,
                    'missing_skills': [skill for skill in required_skills if skill not in user_skills]
                })
                
            # Sort by score in descending order
            recommendations.sort(key=lambda x: x['score'], reverse=True)
            return recommendations[:top_n]
        
        # Continue with sklearn-based approach
        user_skills_text = ' '.join(user_skills)
        user_vector = self.vectorizer.transform([user_skills_text]).toarray()
        
        # Calculate similarity scores
        similarities = cosine_similarity(user_vector, self.skill_matrix).flatten()
        
        # Get top N careers
        top_indices = similarities.argsort()[-top_n:][::-1]
        
        recommendations = []
        for idx in top_indices:
            career = self.career_paths[idx]
            score = float(similarities[idx])
            
            # Get matching and missing skills
            required_skills = career.get('required_skills', [])
            matching_skills = [skill for skill in user_skills if skill in required_skills]
            missing_skills = [skill for skill in required_skills if skill not in user_skills]
            
            recommendations.append({
                'career': career,
                'score': round(score, 2),
                'matching_skills': matching_skills,
                'missing_skills': missing_skills
            })
            
        return recommendations
    
    def get_skill_gaps(self, user_skills, career_title):
        """
        Get skill gaps for a specific career path
        
        Args:
            user_skills (list): List of user's skills
            career_title (str): Career title to analyze
            
        Returns:
            dict: Dictionary with matching and missing skills
        """
        # Find the career by title
        career = None
        for c in self.career_paths:
            if c.get('title').lower() == career_title.lower():
                career = c
                break
        
        if not career:
            return {
                'error': f"Career '{career_title}' not found",
                'matching_skills': [],
                'missing_skills': []
            }
        
        # Find matching and missing skills
        matching_skills = []
        missing_skills = []
        
        for skill in career.get('required_skills', []):
            if skill in user_skills:
                matching_skills.append(skill)
            else:
                missing_skills.append(skill)
        
        return {
            'career': career,
            'matching_skills': matching_skills,
            'missing_skills': missing_skills,
            'match_percentage': round(len(matching_skills) / max(1, len(career.get('required_skills', []))) * 100, 2)
        }
    
    def add_career_path(self, career_data):
        """
        Add a new career path to the dataset
        
        Args:
            career_data (dict): Career path data
            
        Returns:
            bool: Success status
        """
        if not self.career_paths:
            self.career_paths = []
        
        # Generate ID for new career
        max_id = 0
        for career in self.career_paths:
            if career.get('id', 0) > max_id:
                max_id = career.get('id')
        
        career_data['id'] = max_id + 1
        self.career_paths.append(career_data)
        
        # Update vectorizer
        all_skills = []
        for career in self.career_paths:
            skills_text = ' '.join(career.get('required_skills', []))
            all_skills.append(skills_text)
        
        self.vectorizer.fit(all_skills)
        self.skill_matrix = self.vectorizer.transform(all_skills)
        
        # Save updated data
        return self.save_career_paths(self.career_paths)
    
    def get_career_by_id(self, career_id):
        """Get career by ID"""
        for career in self.career_paths:
            if career.get('id') == career_id:
                return career
        return None 