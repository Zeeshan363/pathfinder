import requests
from bs4 import BeautifulSoup
import time
import random
import logging
from datetime import datetime
import json
from ..models import JobListing

logger = logging.getLogger(__name__)

class LinkedInJobScraper:
    """
    A service for scraping job listings from LinkedIn based on search criteria
    """
    
    def __init__(self):
        self.base_url = "https://www.linkedin.com/jobs/search"
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0"
        ]
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def _get_random_user_agent(self):
        """Get a random user agent to avoid detection"""
        return random.choice(self.user_agents)
    
    def _make_request(self, url, params=None):
        """Make an HTTP request with randomized user agent and error handling"""
        self.headers['User-Agent'] = self._get_random_user_agent()
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.error(f"Error making request to {url}: {str(e)}")
            return None
    
    def search_jobs(self, keywords, location, results_limit=25):
        """
        Search for jobs on LinkedIn based on keywords and location
        
        Args:
            keywords (str): Job search keywords (e.g., "software engineer", "data scientist")
            location (str): Job location (e.g., "New York", "Remote")
            results_limit (int): Maximum number of results to return
            
        Returns:
            list: List of job dictionaries containing scraped information
        """
        params = {
            'keywords': keywords,
            'location': location,
            'f_TP': 'true',  # filter for "Easy Apply"
            'sort': 'date',  # sort by most recent
            'pageNum': 0,
            'position': 1
        }
        
        logger.info(f"Searching LinkedIn jobs: keywords='{keywords}', location='{location}'")
        
        jobs = []
        page = 0
        
        # Scrape multiple pages until we reach the results limit
        while len(jobs) < results_limit:
            params['pageNum'] = page
            response = self._make_request(self.base_url, params)
            
            if not response:
                break
                
            soup = BeautifulSoup(response.text, 'html.parser')
            job_cards = soup.find_all('div', class_='base-card')
            
            if not job_cards:
                break
                
            for card in job_cards:
                if len(jobs) >= results_limit:
                    break
                    
                try:
                    job_data = self._extract_job_data(card)
                    if job_data:
                        jobs.append(job_data)
                except Exception as e:
                    logger.error(f"Error extracting job data: {str(e)}")
            
            # LinkedIn sometimes blocks frequent requests, so we'll add a delay
            time.sleep(random.uniform(2, 5))
            page += 1
        
        logger.info(f"Found {len(jobs)} job listings")
        return jobs
    
    def _extract_job_data(self, job_card):
        """Extract job information from a job card element"""
        try:
            # Extract title
            title_elem = job_card.find('h3', class_='base-search-card__title')
            title = title_elem.get_text(strip=True) if title_elem else 'Unknown Title'
            
            # Extract company name
            company_elem = job_card.find('h4', class_='base-search-card__subtitle')
            company = company_elem.get_text(strip=True) if company_elem else 'Unknown Company'
            
            # Extract location
            location_elem = job_card.find('span', class_='job-search-card__location')
            location = location_elem.get_text(strip=True) if location_elem else 'Unknown Location'
            
            # Extract job URL
            link_elem = job_card.find('a', class_='base-card__full-link')
            job_url = link_elem.get('href') if link_elem else None
            
            # Extract job ID from URL if available
            job_id = None
            if job_url and 'view' in job_url:
                job_id = job_url.split('view/')[1].split('/')[0]
            
            # Extract posted date
            date_elem = job_card.find('time', class_='job-search-card__listdate')
            posted_date = date_elem.get('datetime') if date_elem else None
            
            # Extract company logo URL
            logo_elem = job_card.find('img', class_='artdeco-entity-image')
            logo_url = logo_elem.get('data-delayed-url') if logo_elem else None
            
            return {
                'title': title,
                'company': company,
                'location': location,
                'job_url': job_url,
                'job_id': job_id,
                'posted_date': posted_date,
                'logo_url': logo_url,
                'source': 'LinkedIn',
                'scraped_date': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error extracting job data from card: {str(e)}")
            return None
    
    def get_job_details(self, job_url):
        """
        Scrape detailed job information from a specific job URL
        
        Args:
            job_url (str): LinkedIn job URL
            
        Returns:
            dict: Detailed job information
        """
        response = self._make_request(job_url)
        if not response:
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        try:
            # Extract detailed job description
            description_elem = soup.find('div', class_='show-more-less-html__markup')
            description = description_elem.get_text('\n', strip=True) if description_elem else 'No description available'
            
            # Extract skills (if available)
            skills = []
            skills_section = soup.find('section', {'class': 'skills-section'})
            if skills_section:
                skill_items = skills_section.find_all('li')
                skills = [skill.get_text(strip=True) for skill in skill_items]
            
            # Extract seniority level, employment type, job function, etc.
            criteria_elements = soup.find_all('li', class_='description__job-criteria-item')
            criteria = {}
            
            for elem in criteria_elements:
                header = elem.find(class_='description__job-criteria-subheader')
                value = elem.find(class_='description__job-criteria-text')
                
                if header and value:
                    key = header.get_text(strip=True)
                    criteria[key] = value.get_text(strip=True)
            
            return {
                'description': description,
                'skills': skills,
                'criteria': criteria
            }
        except Exception as e:
            logger.error(f"Error extracting detailed job info: {str(e)}")
            return None
    
    def store_job_listings(self, job_listings):
        """
        Store scraped job listings in the database
        
        Args:
            job_listings (list): List of job dictionaries from search_jobs method
            
        Returns:
            int: Number of jobs successfully stored
        """
        count = 0
        for job in job_listings:
            try:
                # Check if job already exists (avoid duplicates)
                existing_job = JobListing.objects.filter(job_id=job.get('job_id')).first()
                if existing_job:
                    # Update existing job with new information
                    existing_job.title = job.get('title')
                    existing_job.company = job.get('company')
                    existing_job.location = job.get('location')
                    existing_job.job_url = job.get('job_url')
                    existing_job.logo_url = job.get('logo_url')
                    existing_job.updated_at = datetime.now()
                    existing_job.save()
                    logger.info(f"Updated existing job: {job.get('title')} at {job.get('company')}")
                else:
                    # Create new job entry
                    job_obj = JobListing(
                        job_id=job.get('job_id'),
                        title=job.get('title'),
                        company=job.get('company'),
                        location=job.get('location'),
                        description="",  # Can be populated later with detailed scraping
                        job_url=job.get('job_url'),
                        logo_url=job.get('logo_url'),
                        source='LinkedIn',
                        posted_date=job.get('posted_date'),
                        data=json.dumps(job)
                    )
                    job_obj.save()
                    count += 1
                    logger.info(f"Stored new job: {job.get('title')} at {job.get('company')}")
            except Exception as e:
                logger.error(f"Error storing job {job.get('title')}: {str(e)}")
        
        return count 