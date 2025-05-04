from django.core.management.base import BaseCommand, CommandError
import json
import os
from api.ml.models.career_chatbot import CareerChatbot
from api.ml.utils.chatbot_trainer import ChatbotTrainer

class Command(BaseCommand):
    help = 'Train the chatbot with new information or patterns'

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(dest='command', help='Command')
        
        # Command to add a single training example
        add_parser = subparsers.add_parser('add', help='Add a training example')
        add_parser.add_argument('--message', required=True, help='User message to add as a pattern')
        add_parser.add_argument('--intent', required=True, help='Intent tag to associate with the message')
        add_parser.add_argument('--response', help='Response to add for this intent (optional)')
        
        # Command to create a new intent
        create_parser = subparsers.add_parser('create', help='Create a new intent')
        create_parser.add_argument('--tag', required=True, help='Intent tag name')
        create_parser.add_argument('--patterns', required=True, help='JSON array of patterns')
        create_parser.add_argument('--responses', required=True, help='JSON array of responses')
        
        # Command to retrain the model
        retrain_parser = subparsers.add_parser('retrain', help='Retrain the model')
        retrain_parser.add_argument('--epochs', type=int, default=50, help='Number of training epochs')
        retrain_parser.add_argument('--learning-rate', type=float, default=0.001, help='Learning rate')
        
        # Command to list available intents
        list_parser = subparsers.add_parser('list', help='List available intents')
        list_parser.add_argument('--tag', help='Intent tag to show details for (optional)')
        
        # Command to import intents from a JSON file
        import_parser = subparsers.add_parser('import', help='Import intents from a JSON file')
        import_parser.add_argument('--file', required=True, help='Path to the JSON file')

    def handle(self, *args, **options):
        trainer = ChatbotTrainer()
        command = options['command']
        
        if command == 'add':
            message = options['message']
            intent = options['intent']
            response = options.get('response')
            
            result = trainer.add_example(message, intent, response)
            if result:
                self.stdout.write(self.style.SUCCESS(f'Successfully added training example to intent "{intent}"'))
            else:
                self.stdout.write(self.style.ERROR(f'Failed to add training example. Intent "{intent}" not found or invalid message.'))
        
        elif command == 'create':
            tag = options['tag']
            
            try:
                patterns = json.loads(options['patterns'])
                if not isinstance(patterns, list):
                    raise ValueError("Patterns must be a JSON array")
            except json.JSONDecodeError:
                raise CommandError('Invalid JSON format for patterns')
            
            try:
                responses = json.loads(options['responses'])
                if not isinstance(responses, list):
                    raise ValueError("Responses must be a JSON array")
            except json.JSONDecodeError:
                raise CommandError('Invalid JSON format for responses')
            
            result = trainer.create_intent(tag, patterns, responses)
            if result:
                self.stdout.write(self.style.SUCCESS(f'Successfully created new intent "{tag}"'))
            else:
                self.stdout.write(self.style.ERROR(f'Failed to create intent. Intent "{tag}" already exists or is invalid.'))
        
        elif command == 'retrain':
            epochs = options['epochs']
            learning_rate = options['learning_rate']
            
            self.stdout.write(f'Retraining chatbot model with {epochs} epochs...')
            result = trainer.retrain_model(epochs, learning_rate)
            if result:
                self.stdout.write(self.style.SUCCESS('Successfully retrained chatbot model'))
            else:
                self.stdout.write(self.style.ERROR('Failed to retrain chatbot model'))
        
        elif command == 'list':
            tag = options.get('tag')
            
            if tag:
                self.stdout.write(f'Showing details for intent "{tag}":')
                trainer.print_intent_info(tag)
            else:
                self.stdout.write('Available intents:')
                intents = trainer.get_available_intents()
                for intent in intents:
                    self.stdout.write(f'- {intent}')
        
        elif command == 'import':
            file_path = options['file']
            
            if not os.path.exists(file_path):
                raise CommandError(f'File not found: {file_path}')
            
            try:
                with open(file_path, 'r') as f:
                    intents_data = json.load(f)
                
                if not isinstance(intents_data, list):
                    raise ValueError("JSON file must contain an array of intents")
                
                success_count = 0
                for intent_data in intents_data:
                    if not all(k in intent_data for k in ('tag', 'patterns', 'responses')):
                        self.stdout.write(self.style.WARNING(f'Skipping intent: missing required fields (tag, patterns, responses)'))
                        continue
                    
                    tag = intent_data['tag']
                    patterns = intent_data['patterns']
                    responses = intent_data['responses']
                    
                    result = trainer.create_intent(tag, patterns, responses)
                    if result:
                        success_count += 1
                
                if success_count > 0:
                    self.stdout.write(self.style.SUCCESS(f'Successfully imported {success_count} intents'))
                    # Retrain the model with the new intents
                    trainer.retrain_model()
                else:
                    self.stdout.write(self.style.WARNING('No intents were imported'))
                
            except json.JSONDecodeError:
                raise CommandError('Invalid JSON format in file')
            except Exception as e:
                raise CommandError(f'Error importing intents: {str(e)}')
        
        else:
            self.stdout.write(self.style.ERROR('Please specify a valid command: add, create, retrain, list, or import'))
            return 