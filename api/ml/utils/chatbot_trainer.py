"""
Utility script for training the chatbot with new information

Example usage:
python manage.py shell
from api.ml.utils.chatbot_trainer import ChatbotTrainer
trainer = ChatbotTrainer()

# Add a training example to an existing intent
trainer.add_example(
    message="How can I become a data analyst?",
    intent="career_information",
    response="To become a data analyst, you'll need skills in SQL, Excel, and data visualization tools."
)

# Create a new intent
trainer.create_intent(
    tag="industry_trends",
    patterns=[
        "What are the trends in tech?",
        "Which industries are growing?",
        "What's the future of healthcare jobs?"
    ],
    responses=[
        "The tech industry continues to grow with AI, cloud computing, and cybersecurity being hot areas.",
        "Healthcare, renewable energy, and tech are among the fastest growing industries."
    ]
)

# Train the model with new data
trainer.retrain_model()
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add the project root to sys.path to import Django modules
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
if BASE_DIR not in sys.path:
    sys.path.append(str(BASE_DIR))

import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pathfinder.settings")
django.setup()

from api.ml.models.career_chatbot import CareerChatbot

logger = logging.getLogger(__name__)

class ChatbotTrainer:
    """Utility class for training the chatbot with new information"""
    
    def __init__(self):
        """Initialize the chatbot model"""
        self.chatbot = CareerChatbot()
        
    def add_example(self, message, intent, response=None):
        """
        Add a training example to an existing intent
        
        Args:
            message (str): The user message to add as a training pattern
            intent (str): The intent tag to associate with this message
            response (str, optional): A response to add for this intent
            
        Returns:
            bool: True if successful, False otherwise
        """
        result = self.chatbot.add_training_example(
            message=message,
            intent_tag=intent,
            response=response
        )
        
        if result:
            print(f"Added new training example to intent '{intent}'")
            return True
        else:
            print(f"Failed to add training example. Intent '{intent}' not found or invalid message.")
            return False
            
    def create_intent(self, tag, patterns, responses):
        """
        Create a new intent category for the chatbot
        
        Args:
            tag (str): The intent tag name
            patterns (list): List of example patterns for this intent
            responses (list): List of responses for this intent
            
        Returns:
            bool: True if successful, False otherwise
        """
        result = self.chatbot.create_new_intent(
            tag=tag,
            patterns=patterns,
            responses=responses
        )
        
        if result:
            print(f"Created new intent '{tag}' with {len(patterns)} patterns and {len(responses)} responses")
            return True
        else:
            print(f"Failed to create intent. Intent '{tag}' already exists or is invalid.")
            return False
            
    def retrain_model(self, epochs=50, learning_rate=0.001):
        """
        Retrain the model with updated intents
        
        Args:
            epochs (int): Number of training epochs
            learning_rate (float): Learning rate for optimizer
            
        Returns:
            bool: True if successful, False otherwise
        """
        print(f"Retraining chatbot model with {epochs} epochs...")
        result = self.chatbot.retrain_model(
            epochs=epochs,
            learning_rate=learning_rate
        )
        
        if result:
            print("Successfully retrained chatbot model")
            return True
        else:
            print("Failed to retrain chatbot model")
            return False
            
    def get_available_intents(self):
        """
        Get a list of all available intent tags
        
        Returns:
            list: List of intent tags
        """
        return [intent['tag'] for intent in self.chatbot.intents]
        
    def print_intent_info(self, tag=None):
        """
        Print information about intents
        
        Args:
            tag (str, optional): The intent tag to show. If None, shows all intents.
        """
        if tag:
            for intent in self.chatbot.intents:
                if intent['tag'] == tag:
                    print(f"\nIntent: {intent['tag']}")
                    print(f"Patterns ({len(intent['patterns'])}):")
                    for pattern in intent['patterns']:
                        print(f"  - {pattern}")
                    print(f"Responses ({len(intent['responses'])}):")
                    for response in intent['responses']:
                        print(f"  - {response}")
                    return
            print(f"Intent '{tag}' not found")
        else:
            print("\nAvailable Intents:")
            for intent in self.chatbot.intents:
                print(f"- {intent['tag']} ({len(intent['patterns'])} patterns, {len(intent['responses'])} responses)")

if __name__ == "__main__":
    # Example usage when run directly
    trainer = ChatbotTrainer()
    
    print("\nChatbot Trainer Utility")
    print("======================")
    print("Available intents:")
    trainer.print_intent_info() 