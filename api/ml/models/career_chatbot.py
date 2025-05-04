import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import json
import os
import re
import random
import logging
from sklearn.feature_extraction.text import CountVectorizer
from .career_recommender import CareerRecommender

logger = logging.getLogger(__name__)

class IntentClassifier(nn.Module):
    """Neural network for classifying user intent from chat messages"""
    
    def __init__(self, input_size, hidden_size, output_size):
        super(IntentClassifier, self).__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, output_size)
        self.dropout = nn.Dropout(0.2)
        
    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.fc2(x)
        return F.log_softmax(x, dim=1)

class CareerChatbot:
    """Simple career guidance chatbot with intent recognition and responses"""
    
    def __init__(self, model_path=None, intents_path=None):
        # Model parameters
        self.input_size = 1000  # Bag of words feature size
        self.hidden_size = 100
        self.output_size = 8  # Number of intents
        
        # Initialize model
        self.model = IntentClassifier(self.input_size, self.hidden_size, self.output_size)
        
        # Directory paths
        module_dir = os.path.dirname(os.path.abspath(__file__))
        self.model_path = model_path or os.path.join(module_dir, '../../ml/data/chatbot_model.pth')
        self.intents_path = intents_path or os.path.join(module_dir, '../../ml/data/chatbot_intents.json')
        
        # Load intents and initialize vectorizer
        self.intents = self._load_intents()
        self.vectorizer = CountVectorizer(max_features=self.input_size)
        
        # Connect to career recommender
        self.career_recommender = CareerRecommender()
        
        # Train vectorizer on intents patterns
        patterns = []
        for intent in self.intents:
            patterns.extend(intent['patterns'])
        
        if patterns:
            self.vectorizer.fit(patterns)
        
        # Try to load pre-trained model if it exists
        try:
            if os.path.exists(self.model_path):
                self.model.load_state_dict(torch.load(self.model_path))
                self.model.eval()
                logger.info(f"Loaded pre-trained chatbot model from {self.model_path}")
        except Exception as e:
            logger.warning(f"Could not load pre-trained chatbot model: {str(e)}")
            # Train a basic model if none exists
            self._train_basic_model()
    
    def _load_intents(self):
        """Load intents data from JSON file or create sample intents"""
        try:
            if os.path.exists(self.intents_path):
                with open(self.intents_path, 'r') as f:
                    return json.load(f)
            else:
                # Create sample intents if file doesn't exist
                logger.warning(f"Intents file not found at {self.intents_path}, using sample intents.")
                intents = self._get_sample_intents()
                self._save_intents(intents)
                return intents
        except Exception as e:
            logger.error(f"Error loading intents: {str(e)}")
            return self._get_sample_intents()
    
    def _get_sample_intents(self):
        """Create sample intents for chatbot training"""
        return [
            {
                "tag": "greeting",
                "patterns": [
                    "Hi", "Hey", "Hello", "Good day", "Greetings", "What's up",
                    "How are you", "Is anyone there?", "Hello there", "Hi there"
                ],
                "responses": [
                    "Hello! How can I help you with your career planning?",
                    "Hi there! I'm your career guidance assistant. What would you like to know about careers?",
                    "Hey! I can help you find the right career path. What skills do you have?"
                ]
            },
            {
                "tag": "goodbye",
                "patterns": [
                    "Bye", "See you later", "Goodbye", "Take care", "I'm leaving",
                    "Have a good day", "See ya", "Till next time", "Farewell"
                ],
                "responses": [
                    "Goodbye! Feel free to come back if you have more career questions.",
                    "See you later! Best of luck with your career journey.",
                    "Take care! Remember to keep building your skills for your dream career."
                ]
            },
            {
                "tag": "thanks",
                "patterns": [
                    "Thanks", "Thank you", "That's helpful", "Appreciate it", "Thanks a lot",
                    "Thanks for the help", "Thank you so much", "That was helpful"
                ],
                "responses": [
                    "You're welcome! Happy to help with your career planning.",
                    "Anytime! Your career development is important.",
                    "No problem! Let me know if you need more career guidance."
                ]
            },
            {
                "tag": "career_recommendation",
                "patterns": [
                    "What career should I pursue?", "What job is right for me?", "Suggest a career for me",
                    "Help me find a suitable career", "What careers match my skills?",
                    "Career recommendations", "What should I be when I grow up?",
                    "What professions match my interests?", "Help me choose a career path"
                ],
                "responses": [
                    "I can help you find a suitable career! What skills do you have?",
                    "Finding the right career path is important. Could you tell me about your skills and interests?",
                    "To recommend careers, I need to know your skills. What are you good at?"
                ]
            },
            {
                "tag": "skill_gap",
                "patterns": [
                    "What skills do I need for", "How do I become a", "Skills required for",
                    "What should I learn to be a", "Skill gap for", "What am I missing to become",
                    "How to prepare for career in", "Requirements for", "Qualifications for"
                ],
                "responses": [
                    "I can analyze skill gaps for specific careers. Which career are you interested in?",
                    "To identify skill gaps, I need to know which career you're targeting and your current skills.",
                    "I'll help you bridge the gap to your desired career. What career are you interested in, and what skills do you already have?"
                ]
            },
            {
                "tag": "course_recommendation",
                "patterns": [
                    "What should I study?", "Recommend courses for me", "What courses should I take?",
                    "How to learn", "Best way to learn", "Suggest courses for",
                    "How can I improve my skills in", "Training programs for", "Certifications for"
                ],
                "responses": [
                    "To recommend courses, I need to know what career you're targeting. Could you share more details?",
                    "I can suggest courses once I understand your career goals and current skills.",
                    "Learning resources depend on your target career and skill level. What are you interested in?"
                ]
            },
            {
                "tag": "career_information",
                "patterns": [
                    "Tell me about being a", "What does a do", "Day in the life of a",
                    "Responsibilities of", "What is it like to be a", "Career information for",
                    "Salary for", "How much does a earn", "Job outlook for",
                    "Is a good career", "Future of"
                ],
                "responses": [
                    "I can provide information about specific careers. Which one would you like to learn about?",
                    "Career information includes responsibilities, skills required, and salary expectations. Which career are you curious about?",
                    "I have details on various careers. Which specific profession would you like to know more about?"
                ]
            },
            {
                "tag": "fallback",
                "patterns": [],
                "responses": [
                    "I'm not sure I understand. Could you rephrase that?",
                    "I'm still learning about careers. Could you ask in a different way?",
                    "I'm not sure how to help with that. I can provide career recommendations, skill gap analysis, and career information. How can I assist you?"
                ]
            }
        ]
    
    def _save_intents(self, intents):
        """Save intents data to JSON file"""
        try:
            data_dir = os.path.dirname(self.intents_path)
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
            with open(self.intents_path, 'w') as f:
                json.dump(intents, f, indent=2)
            logger.info(f"Intents saved to {self.intents_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving intents: {str(e)}")
            return False
    
    def _train_basic_model(self, epochs=100, learning_rate=0.001):
        """Train a basic intent classification model if none exists"""
        # Prepare training data
        X_train = []
        y_train = []
        
        for i, intent in enumerate(self.intents):
            for pattern in intent['patterns']:
                X_train.append(pattern)
                y_train.append(i)
        
        if not X_train:
            logger.error("No training data available for chatbot")
            return False
        
        # Vectorize patterns
        X_vectors = self.vectorizer.transform(X_train).toarray()
        X_tensors = torch.FloatTensor(X_vectors)
        y_tensors = torch.LongTensor(y_train)
        
        # Define loss function and optimizer
        criterion = nn.NLLLoss()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate)
        
        # Train the model
        self.model.train()
        for epoch in range(epochs):
            optimizer.zero_grad()
            outputs = self.model(X_tensors)
            loss = criterion(outputs, y_tensors)
            loss.backward()
            optimizer.step()
            
            if (epoch + 1) % 20 == 0:
                logger.info(f'Epoch {epoch+1}/{epochs}, Loss: {loss.item():.4f}')
        
        # Save the model
        try:
            model_dir = os.path.dirname(self.model_path)
            if not os.path.exists(model_dir):
                os.makedirs(model_dir)
            torch.save(self.model.state_dict(), self.model_path)
            logger.info(f"Chatbot model saved to {self.model_path}")
        except Exception as e:
            logger.error(f"Error saving chatbot model: {str(e)}")
        
        self.model.eval()
        return True
    
    def process_message(self, message, user_skills=None, user_interests=None, user_context=None):
        """
        Process user message and generate a response
        
        Args:
            message (str): User's message text
            user_skills (list, optional): User's skills for personalization
            user_interests (list, optional): User's interests for personalization
            user_context (dict, optional): Conversation context
            
        Returns:
            dict: Response with text and any additional information
        """
        # Preprocess message
        message = message.strip().lower()
        
        # Initialize context if none provided
        if user_context is None:
            user_context = {
                'last_intent': None,
                'mentioned_career': None,
                'awaiting_skills': False,
                'awaiting_career': False
            }
        
        # Check for specific career intent in the message
        career_match = re.search(r'(career|job|profession)\s+(?:in|as)\s+(?:a|an)?\s+([a-z\s]+)(?:\?|\.|\s|$)', message)
        career_match2 = re.search(r'(become|being|be)\s+(?:a|an)?\s+([a-z\s]+?)(?:\?|\.|\s|$)', message)
        
        if career_match:
            user_context['mentioned_career'] = career_match.group(2).strip()
        elif career_match2:
            user_context['mentioned_career'] = career_match2.group(2).strip()
        
        # Check for skill listing in the message
        skills_detected = []
        if self.career_recommender.career_paths:
            # Extract all skills from career paths
            all_skills = set()
            for career in self.career_recommender.career_paths:
                all_skills.update(skill.lower() for skill in career.get('required_skills', []))
            
            # Check if any known skills are mentioned in the message
            for skill in all_skills:
                if re.search(r'\b' + re.escape(skill.lower()) + r'\b', message):
                    skills_detected.append(skill)
        
        # Process intent if we have an existing model
        try:
            # Vectorize the message
            message_vec = self.vectorizer.transform([message]).toarray()
            message_tensor = torch.FloatTensor(message_vec)
            
            # Get predicted intent
            output = self.model(message_tensor)
            _, predicted = torch.max(output, 1)
            intent_idx = predicted.item()
            
            intent_tag = self.intents[intent_idx]['tag']
        except Exception as e:
            logger.error(f"Error predicting intent: {str(e)}")
            intent_tag = "fallback"
        
        # Special case: career_recommendation with skills detected
        if intent_tag == "career_recommendation" and (skills_detected or user_skills):
            skills_to_use = skills_detected or user_skills
            if skills_to_use:
                # Use the career recommender to get recommendations
                recommendations = self.career_recommender.get_recommendations(
                    user_skills=skills_to_use, 
                    user_interests=user_interests,
                    top_n=3
                )
                
                if recommendations:
                    # Generate response with recommendations
                    response_text = "Based on your skills, here are some career recommendations:\n\n"
                    for i, rec in enumerate(recommendations, 1):
                        career = rec['career']
                        score = rec['relevance_score']
                        matching = rec['matching_skills']
                        missing = rec['missing_skills']
                        
                        response_text += f"{i}. {career['title']} (Match: {score:.2f})\n"
                        response_text += f"   Description: {career['description']}\n"
                        response_text += f"   Matching skills: {', '.join(matching[:3])}\n"
                        if missing:
                            response_text += f"   Skills to develop: {', '.join(missing[:3])}\n"
                        response_text += "\n"
                    
                    user_context['last_intent'] = "career_recommendation_with_skills"
                    return {
                        'text': response_text.strip(),
                        'context': user_context,
                        'recommendations': recommendations
                    }
            
            # If we don't have skills yet, ask for them
            user_context['awaiting_skills'] = True
            user_context['last_intent'] = "career_recommendation"
            return {
                'text': random.choice(self.intents[intent_idx]['responses']),
                'context': user_context
            }
        
        # Special case: skill gap with mentioned career
        elif intent_tag == "skill_gap" and user_context.get('mentioned_career'):
            career_title = user_context['mentioned_career']
            if user_skills:
                # Use the career recommender to get skill gap analysis
                skill_gap = self.career_recommender.get_skill_gaps(
                    user_skills=user_skills,
                    career_title=career_title
                )
                
                if 'error' not in skill_gap:
                    # Generate response with skill gap analysis
                    career = skill_gap['career']
                    matching = skill_gap['matching_skills']
                    missing = skill_gap['missing_skills']
                    match_pct = skill_gap['match_percentage']
                    
                    response_text = f"For a career as a {career['title']}:\n\n"
                    response_text += f"You have {match_pct}% of the required skills.\n\n"
                    
                    if matching:
                        response_text += f"Your matching skills: {', '.join(matching)}\n\n"
                    
                    if missing:
                        response_text += f"Skills to develop: {', '.join(missing)}\n\n"
                    
                    response_text += f"This career typically requires: {', '.join(career['education'][:2])}"
                    
                    user_context['last_intent'] = "skill_gap_with_career"
                    return {
                        'text': response_text,
                        'context': user_context,
                        'skill_gap': skill_gap
                    }
                else:
                    response_text = f"I couldn't find information about a career as a {career_title}. Could you try another career title?"
                    return {
                        'text': response_text,
                        'context': user_context
                    }
            else:
                # If we don't have skills, ask for them
                user_context['awaiting_skills'] = True
                user_context['last_intent'] = "skill_gap"
                return {
                    'text': f"To analyze the skill gap for a {career_title}, I need to know your current skills. What skills do you have?",
                    'context': user_context
                }
        
        # Special case: career_information with mentioned career
        elif intent_tag == "career_information" and user_context.get('mentioned_career'):
            career_title = user_context['mentioned_career']
            
            # Find career information
            career = None
            for c in self.career_recommender.career_paths:
                if c['title'].lower() == career_title.lower() or career_title.lower() in c['title'].lower():
                    career = c
                    break
            
            if career:
                # Generate response with career information
                response_text = f"About a career as a {career['title']}:\n\n"
                response_text += f"Description: {career['description']}\n\n"
                response_text += f"Required Skills: {', '.join(career['required_skills'][:5])}"
                if len(career['required_skills']) > 5:
                    response_text += f" and {len(career['required_skills']) - 5} more\n\n"
                else:
                    response_text += "\n\n"
                
                response_text += f"Education: {', '.join(career['education'])}\n\n"
                response_text += f"Salary Range: {career['salary_range']}\n"
                response_text += f"Growth Potential: {career['growth_potential']}\n"
                response_text += f"Industry: {career['industry']}"
                
                user_context['last_intent'] = "career_information_with_career"
                return {
                    'text': response_text,
                    'context': user_context,
                    'career': career
                }
            else:
                response_text = f"I don't have specific information about a career as a {career_title}. Would you like to know about a different career?"
                user_context['awaiting_career'] = True
                user_context['last_intent'] = "career_information"
                return {
                    'text': response_text,
                    'context': user_context
                }
        
        # Handle awaiting skills from previous message
        elif user_context.get('awaiting_skills') and skills_detected:
            user_context['awaiting_skills'] = False
            
            if user_context.get('last_intent') == "career_recommendation":
                # Process as career recommendation with detected skills
                recommendations = self.career_recommender.get_recommendations(
                    user_skills=skills_detected, 
                    user_interests=user_interests,
                    top_n=3
                )
                
                if recommendations:
                    # Generate response with recommendations
                    response_text = "Based on your skills, here are some career recommendations:\n\n"
                    for i, rec in enumerate(recommendations, 1):
                        career = rec['career']
                        score = rec['relevance_score']
                        matching = rec['matching_skills']
                        missing = rec['missing_skills']
                        
                        response_text += f"{i}. {career['title']} (Match: {score:.2f})\n"
                        response_text += f"   Description: {career['description']}\n"
                        response_text += f"   Matching skills: {', '.join(matching[:3])}\n"
                        if missing:
                            response_text += f"   Skills to develop: {', '.join(missing[:3])}\n"
                        response_text += "\n"
                    
                    user_context['last_intent'] = "career_recommendation_with_skills"
                    return {
                        'text': response_text.strip(),
                        'context': user_context,
                        'recommendations': recommendations
                    }
                else:
                    return {
                        'text': "I couldn't find any career recommendations based on those skills. Could you share more skills or different ones?",
                        'context': user_context
                    }
            elif user_context.get('last_intent') == "skill_gap" and user_context.get('mentioned_career'):
                # Process as skill gap with detected skills
                career_title = user_context['mentioned_career']
                skill_gap = self.career_recommender.get_skill_gaps(
                    user_skills=skills_detected,
                    career_title=career_title
                )
                
                if 'error' not in skill_gap:
                    # Generate response with skill gap analysis
                    career = skill_gap['career']
                    matching = skill_gap['matching_skills']
                    missing = skill_gap['missing_skills']
                    match_pct = skill_gap['match_percentage']
                    
                    response_text = f"For a career as a {career['title']}:\n\n"
                    response_text += f"You have {match_pct}% of the required skills.\n\n"
                    
                    if matching:
                        response_text += f"Your matching skills: {', '.join(matching)}\n\n"
                    
                    if missing:
                        response_text += f"Skills to develop: {', '.join(missing)}\n\n"
                    
                    response_text += f"This career typically requires: {', '.join(career['education'][:2])}"
                    
                    user_context['last_intent'] = "skill_gap_with_career"
                    return {
                        'text': response_text,
                        'context': user_context,
                        'skill_gap': skill_gap
                    }
                else:
                    response_text = f"I couldn't find information about a career as a {career_title}. Could you try another career title?"
                    return {
                        'text': response_text,
                        'context': user_context
                    }
        
        # Default response based on intent
        for intent in self.intents:
            if intent['tag'] == intent_tag:
                user_context['last_intent'] = intent_tag
                return {
                    'text': random.choice(intent['responses']),
                    'context': user_context
                }
        
        # Fallback response
        fallback_responses = next((intent['responses'] for intent in self.intents if intent['tag'] == 'fallback'), 
                                 ["I'm not sure how to help with that."])
        user_context['last_intent'] = "fallback"
        return {
            'text': random.choice(fallback_responses),
            'context': user_context
        } 