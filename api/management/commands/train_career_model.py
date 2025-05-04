from django.core.management.base import BaseCommand
import argparse
import logging
from pathfinder.api.ml.models.career_recommender import CareerRecommender

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Train the career recommendation model'

    def add_arguments(self, parser):
        parser.add_argument(
            '--epochs',
            type=int,
            default=100,
            help='Number of training epochs'
        )
        parser.add_argument(
            '--learning-rate',
            type=float,
            default=0.001,
            help='Learning rate for training'
        )
        parser.add_argument(
            '--career-path',
            type=str,
            help='Optional path to a JSON file with career paths data'
        )

    def handle(self, *args, **options):
        epochs = options['epochs']
        learning_rate = options['learning_rate']
        career_path = options.get('career_path')
        
        self.stdout.write(self.style.NOTICE('Initializing career recommendation model...'))
        
        try:
            recommender = CareerRecommender(career_paths_file=career_path)
            self.stdout.write(self.style.SUCCESS(f'Model initialized with {len(recommender.career_paths)} career paths'))
            
            self.stdout.write(self.style.NOTICE(f'Training model with {epochs} epochs and learning rate {learning_rate}...'))
            result = recommender.train_model(epochs=epochs, learning_rate=learning_rate)
            
            self.stdout.write(self.style.SUCCESS('Model training completed!'))
            self.stdout.write(f'Final loss: {result["final_loss"]:.4f}')
            self.stdout.write(f'Model saved to: {result["model_path"]}')
            
            return True
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error training model: {str(e)}'))
            logger.error(f"Error in train_career_model command: {str(e)}", exc_info=True)
            return False 