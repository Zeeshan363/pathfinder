from django.shortcuts import get_object_or_404
from django.http import Http404
from api.models import User, Profile

class CareerPath:
    def __init__(self, id, name, description, required_skills, related_interests, match_score=None):
        self.id = id
        self.name = name
        self.description = description
        self.required_skills = required_skills
        self.related_interests = related_interests
        self.match_score = match_score
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'requiredSkills': self.required_skills,
            'relatedInterests': self.related_interests,
            'matchScore': self.match_score
        }

class RecommendationService:
    def __init__(self):
        self.career_paths = [
            CareerPath(
                id=1,
                name='Data Science',
                description='Career in analyzing and interpreting complex data to help organizations make better decisions.',
                required_skills=['python', 'r', 'statistics', 'machine learning', 'sql', 'data visualization'],
                related_interests=['math', 'statistics', 'analytics', 'technology', 'research'],
            ),
            CareerPath(
                id=2,
                name='Web Development',
                description='Building and maintaining websites and web applications.',
                required_skills=['html', 'css', 'javascript', 'react', 'node', 'express', 'angular'],
                related_interests=['design', 'coding', 'technology', 'creativity'],
            ),
            CareerPath(
                id=3,
                name='Cybersecurity',
                description='Protecting systems, networks, and programs from digital attacks.',
                required_skills=['network security', 'encryption', 'ethical hacking', 'risk management', 'security assessment'],
                related_interests=['security', 'technology', 'privacy', 'problem solving'],
            ),
            CareerPath(
                id=4,
                name='Mobile App Development',
                description='Creating applications for mobile devices like smartphones and tablets.',
                required_skills=['swift', 'kotlin', 'react native', 'flutter', 'mobile ui design'],
                related_interests=['mobile technology', 'design', 'user experience', 'creativity'],
            ),
            CareerPath(
                id=5,
                name='Artificial Intelligence',
                description='Developing AI systems and applications that can perform tasks that typically require human intelligence.',
                required_skills=['machine learning', 'deep learning', 'neural networks', 'python', 'tensorflow', 'pytorch'],
                related_interests=['ai', 'research', 'technology', 'innovation', 'problem solving'],
            )
        ]

    def get_career_path_recommendations(self, user_id):
        try:
            user = User.objects.select_related('profile').get(id=user_id)
            if not hasattr(user, 'profile') or not user.profile:
                raise Http404('User profile not found')
        except User.DoesNotExist:
            raise Http404('User not found')

        user_skills = []
        if user.profile.technical_skills:
            user_skills.extend(user.profile.technical_skills)
        if user.profile.soft_skills:
            user_skills.extend(user.profile.soft_skills)
        user_skills = [skill.lower() for skill in user_skills]
        
        user_interests = []
        if user.profile.interests:
            user_interests = [interest.lower() for interest in user.profile.interests]

        recommended_paths = []
        for path in self.career_paths:
            # Calculate skill match
            skill_match_count = sum(
                1 for skill in path.required_skills 
                if any(user_skill.find(skill) != -1 or skill.find(user_skill) != -1 for user_skill in user_skills)
            )
            
            skill_match_score = 0
            if path.required_skills:
                skill_match_score = (skill_match_count / len(path.required_skills)) * 100
            
            # Calculate interest match
            interest_match_count = sum(
                1 for interest in path.related_interests 
                if any(user_interest.find(interest) != -1 or interest.find(user_interest) != -1 for user_interest in user_interests)
            )
            
            interest_match_score = 0
            if path.related_interests:
                interest_match_score = (interest_match_count / len(path.related_interests)) * 100
            
            # Calculate overall match score (weighted)
            match_score = (skill_match_score * 0.7) + (interest_match_score * 0.3)
            
            # Create a new CareerPath instance with the calculated match score
            recommended_path = CareerPath(
                id=path.id,
                name=path.name,
                description=path.description,
                required_skills=path.required_skills,
                related_interests=path.related_interests,
                match_score=round(match_score, 2)
            )
            
            recommended_paths.append(recommended_path)
        
        # Sort by match score in descending order
        recommended_paths.sort(key=lambda x: x.match_score, reverse=True)
        
        return recommended_paths