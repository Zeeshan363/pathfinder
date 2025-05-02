from django.core.management.base import BaseCommand
from api.services.job_scraper_service import LinkedInJobScraper
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Scrape job listings from LinkedIn'

    def add_arguments(self, parser):
        parser.add_argument('--keywords', required=True, type=str, help='Keywords to search for')
        parser.add_argument('--location', type=str, default='', help='Location to search in')
        parser.add_argument('--limit', type=int, default=25, help='Maximum number of jobs to scrape')

    def handle(self, *args, **options):
        keywords = options['keywords']
        location = options['location']
        limit = options['limit']
        
        self.stdout.write(self.style.SUCCESS(f'Starting job scraping for keywords: "{keywords}" in location: "{location}"'))
        
        scraper = LinkedInJobScraper()
        
        try:
            # Scrape jobs
            self.stdout.write('Scraping jobs...')
            job_listings = scraper.search_jobs(
                keywords=keywords,
                location=location,
                results_limit=limit
            )
            
            if not job_listings:
                self.stdout.write(self.style.WARNING('No job listings found.'))
                return
                
            self.stdout.write(self.style.SUCCESS(f'Found {len(job_listings)} job listings'))
            
            # Store jobs in database
            self.stdout.write('Storing job listings in database...')
            jobs_stored = scraper.store_job_listings(job_listings)
            
            self.stdout.write(self.style.SUCCESS(f'Successfully stored {jobs_stored} job listings'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}')) 