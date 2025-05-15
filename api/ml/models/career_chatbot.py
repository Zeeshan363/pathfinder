try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
import numpy as np
import json
import os
import re
import random
import logging
try:
    from sklearn.feature_extraction.text import CountVectorizer
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
from .career_recommender import CareerRecommender

logger = logging.getLogger(__name__)

if TORCH_AVAILABLE:
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
else:
    # Fallback placeholder class when torch is not available
    class IntentClassifier:
        def __init__(self, input_size, hidden_size, output_size):
            self.input_size = input_size
            self.hidden_size = hidden_size
            self.output_size = output_size

class CareerChatbot:
    """Simple career guidance chatbot with intent recognition and responses"""
    
    def __init__(self, model_path=None, intents_path=None):
        # Model parameters
        self.input_size = 100  # Reduced from 1000 to match actual vocabulary size
        self.hidden_size = 64  # Reduced from 100 for better training
        
        # Directory paths
        module_dir = os.path.dirname(os.path.abspath(__file__))
        self.model_path = model_path or os.path.join(module_dir, '../../ml/data/chatbot_model.pth')
        self.intents_path = intents_path or os.path.join(module_dir, '../../ml/data/chatbot_intents.json')
        
        # Load intents and initialize vectorizer
        self.intents = self._load_intents()
        
        # Set output size based on number of intents
        self.output_size = len(self.intents)
        
        # Initialize model with dynamic output size
        self.model = IntentClassifier(self.input_size, self.hidden_size, self.output_size)
        
        if SKLEARN_AVAILABLE:
            self.vectorizer = CountVectorizer(max_features=self.input_size)
            
            # Train vectorizer on intents patterns
            patterns = []
            for intent in self.intents:
                patterns.extend(intent['patterns'])
            
            if patterns:
                self.vectorizer.fit(patterns)
        
        # Connect to career recommender
        self.career_recommender = CareerRecommender()
        
        # Try to load pre-trained model if it exists
        if TORCH_AVAILABLE:
            try:
                if os.path.exists(self.model_path):
                    self.model.load_state_dict(torch.load(self.model_path))
                    self.model.eval()
                    logger.info(f"Loaded pre-trained chatbot model from {self.model_path}")
                else:
                    # Train a basic model if none exists
                    logger.info("No pre-trained model found, training new model...")
                    self._train_basic_model()
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
        if not TORCH_AVAILABLE or not SKLEARN_AVAILABLE:
            logger.error("PyTorch or scikit-learn not available, cannot train model")
            return False
            
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
        
        # Recreate and fit vectorizer with all patterns
        self.vectorizer = CountVectorizer(max_features=self.input_size)
        self.vectorizer.fit(X_train)
        
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
        
        # Check for specific skills in the message directly
        skill_keywords = ["python", "java", "javascript", "html", "css", "machine learning", "data analysis", 
                         "data science", "sql", "database", "aws", "cloud", "react", "angular", "vue", 
                         "node", "excel", "tableau", "power bi", "statistics", "ai", "artificial intelligence"]
        
        for skill in skill_keywords:
            if skill in message.lower() and skill not in skills_detected:
                skills_detected.append(skill)
        
        # Special case for career questions with skills
        if "career" in message.lower() or "job" in message.lower() or "profession" in message.lower():
            if skills_detected:
                # Direct career recommendation for detected skills
                return self._generate_career_recommendation(skills_detected, user_context)
            elif "python" in message.lower() and "data analysis" in message.lower():
                # Special case for Python and data analysis
                python_response = {
                    'text': "Based on your Python and data analysis skills, here are excellent career paths to consider:\n\n"
                           "1. Data Scientist - Combining statistics, programming, and domain knowledge\n"
                           "2. Machine Learning Engineer - Implementing ML models and algorithms\n"
                           "3. Data Analyst - Analyzing and interpreting data sets\n"
                           "4. Business Intelligence Analyst - Creating dashboards and visualizations\n"
                           "5. Research Analyst - Applying analytical techniques to research problems\n\n"
                           "Each of these leverages your programming and analytical abilities. Would you like more details on any of these careers?",
                    'context': {
                        'last_intent': "career_recommendation_with_skills",
                        'mentioned_career': None,
                        'awaiting_skills': False,
                        'awaiting_career': False
                    }
                }
                return python_response
        
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
        
        # Handle career recommendation intent explicitly
        if intent_tag == "career_recommendation":
            if skills_detected or user_skills:
                return self._generate_career_recommendation(skills_detected or user_skills, user_context, user_interests)
            else:
                # If no skills detected, ask for skills
                user_context['awaiting_skills'] = True
                user_context['last_intent'] = "career_recommendation"
                return {
                    'text': random.choice([
                        "I can help you find a suitable career! What skills do you have?",
                        "Finding the right career path is important. Could you tell me about your skills and interests?",
                        "To recommend careers, I need to know your skills. What are you good at?"
                    ]),
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
    
    def add_training_example(self, message, intent_tag, response=None):
        """
        Add a new training example to the intents and optionally a new response
        
        Args:
            message (str): The user message to add as a training pattern
            intent_tag (str): The intent tag to associate with this message
            response (str, optional): A response to add for this intent
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not message or not intent_tag:
            return False
        
        # Normalize the message
        message = message.strip()
        
        # Find the matching intent
        for intent in self.intents:
            if intent['tag'] == intent_tag:
                # Add the new pattern if it doesn't exist
                if message not in intent['patterns']:
                    intent['patterns'].append(message)
                    logger.info(f"Added new pattern to {intent_tag}: {message}")
                
                # Optionally add a new response
                if response and response not in intent['responses']:
                    intent['responses'].append(response)
                    logger.info(f"Added new response to {intent_tag}: {response}")
                
                # Save the updated intents
                self._save_intents(self.intents)
                
                # Update the vectorizer with the new pattern
                self._update_vectorizer([message])
                
                return True
        
        # If we get here, the intent tag wasn't found
        logger.warning(f"Intent tag not found: {intent_tag}")
        return False
    
    def _update_vectorizer(self, new_patterns):
        """Update the vectorizer with new patterns"""
        try:
            # Get all existing patterns
            all_patterns = []
            for intent in self.intents:
                all_patterns.extend(intent['patterns'])
            
            # Retrain the vectorizer with all patterns
            self.vectorizer = CountVectorizer(max_features=self.input_size)
            self.vectorizer.fit(all_patterns)
            logger.info("Updated vectorizer with new patterns")
        except Exception as e:
            logger.error(f"Error updating vectorizer: {str(e)}")
    
    def retrain_model(self, epochs=50, learning_rate=0.001):
        """
        Retrain the model with updated intents
        
        Args:
            epochs (int): Number of training epochs
            learning_rate (float): Learning rate for optimizer
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Update output size based on current number of intents
            self.output_size = len(self.intents)
            
            # Recreate the model with the updated output size
            self.model = IntentClassifier(self.input_size, self.hidden_size, self.output_size)
            
            # Train the model
            result = self._train_basic_model(epochs=epochs, learning_rate=learning_rate)
            if result:
                logger.info("Successfully retrained chatbot model with new data")
            return result
        except Exception as e:
            logger.error(f"Error retraining model: {str(e)}")
            return False
            
    def create_new_intent(self, tag, patterns=None, responses=None):
        """
        Create a new intent category for the chatbot
        
        Args:
            tag (str): The intent tag name
            patterns (list): List of example patterns for this intent
            responses (list): List of responses for this intent
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not tag:
            return False
            
        # Check if intent already exists
        for intent in self.intents:
            if intent['tag'] == tag:
                return False  # Intent already exists
                
        # Create new intent
        new_intent = {
            "tag": tag,
            "patterns": patterns or [],
            "responses": responses or []
        }
        
        # Add to intents list
        self.intents.append(new_intent)
        
        # Save the updated intents
        self._save_intents(self.intents)
        
        # Update the vectorizer if patterns were provided
        if patterns:
            self._update_vectorizer(patterns)
            
        # Update output size for the model
        self.output_size = len(self.intents)
        
        logger.info(f"Created new intent: {tag}")
        return True

    def _generate_career_recommendation(self, skills, user_context, interests=None):
        """Generate a career recommendation response based on skills"""
        try:
            # Use the career recommender to get recommendations
            recommendations = self.career_recommender.get_recommendations(
                user_skills=skills, 
                user_interests=interests,
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
                # Fallback response for skills without recommendations
                default_careers = {
                    'python': ['Data Scientist', 'Software Developer', 'DevOps Engineer', 'Machine Learning Engineer'],
                    'java': ['Backend Developer', 'Android Developer', 'Enterprise Architect', 'Full Stack Developer'],
                    'javascript': ['Frontend Developer', 'Full Stack Developer', 'Web Developer', 'UI Engineer'],
                    'data analysis': ['Data Analyst', 'Business Analyst', 'Business Intelligence Developer', 'Market Research Analyst'],
                    'machine learning': ['Machine Learning Engineer', 'AI Specialist', 'Research Scientist', 'NLP Engineer'],
                    'sql': ['Database Administrator', 'Data Engineer', 'Business Intelligence Analyst', 'Systems Analyst']
                }
                
                # Check for relevant careers based on skills
                suggested_careers = []
                for skill in skills:
                    skill_lower = skill.lower()
                    for key, careers in default_careers.items():
                        if key in skill_lower:
                            suggested_careers.extend(careers)
                
                # Remove duplicates and limit to 5
                suggested_careers = list(dict.fromkeys(suggested_careers))[:5]
                
                if suggested_careers:
                    response_text = f"Based on your skills, here are some recommended career paths:\n\n"
                    for i, career in enumerate(suggested_careers, 1):
                        response_text += f"{i}. {career}\n"
                    response_text += "\nWould you like more information about any of these careers?"
                    
                    user_context['last_intent'] = "career_recommendation_with_skills"
                    return {
                        'text': response_text,
                        'context': user_context
                    }
                else:
                    # If no specific careers found, give general advice
                    response_text = "Based on your skills, you might consider careers in technology, data, or software development fields. Could you share more specific skills or interests so I can give you better recommendations?"
                    user_context['last_intent'] = "career_recommendation"
                    return {
                        'text': response_text,
                        'context': user_context
                    }
        except Exception as e:
            logger.error(f"Error generating career recommendation: {str(e)}")
            # Provide a fallback career recommendation
            response_text = "Based on typical skill combinations, you might consider careers like Software Developer, Data Analyst, Project Manager, or Business Analyst. What specific aspect of these careers interests you most?"
            user_context['last_intent'] = "career_recommendation"
            return {
                'text': response_text,
                'context': user_context
            } 