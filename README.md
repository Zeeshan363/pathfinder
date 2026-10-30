# Pathfinder

Pathfinder is the backend for an AI-assisted career guidance platform. It is a Django REST API that handles user accounts and profiles, recommends career paths from a user's skills and interests, analyses skill gaps, runs a career guidance chatbot, and scrapes and recommends job listings.

## Features

- **Authentication**: registration, and JWT login and refresh. Users have a role: `STUDENT`, `PROFESSIONAL`, `COUNSELOR` or `ADMIN`.
- **Profiles**: skills, languages, interests, career goals, education and work experience.
- **Career recommendations**: match a user's skills to career paths (TF-IDF plus a PyTorch embedding model).
- **Skill gap analysis**: compare a user's skills with what a target career needs.
- **Career chatbot**: a PyTorch intent classifier trained on `api/ml/data/chatbot_intents.json`. It is publicly accessible.
- **Jobs**: scrape listings from LinkedIn, then filter, search and get personalised job recommendations.
- **Feedback**: users submit feedback and admins review it and update its status.

## Tech stack

- Python 3.10+, Django 4.2, Django REST Framework
- PostgreSQL (uses `ArrayField`)
- `djangorestframework-simplejwt` for authentication
- PyTorch, scikit-learn and NumPy for the ML models
- BeautifulSoup and Requests for job scraping

## Project structure

```
pathfinder/
├── manage.py
├── requirements.txt
├── pathfinder/              # Django project settings and root URLs
└── api/
    ├── models.py            # User, Profile, Education, Experience, JobListing, Feedback
    ├── permissions.py       # IsAdminRole
    ├── urls.py              # API routes
    ├── views/               # auth, profile, recommendation, career, job, feedback views
    ├── serializers/
    ├── services/            # recommendation_service, job_scraper_service
    ├── ml/
    │   ├── models/          # career_recommender, career_chatbot, job_recommender
    │   ├── utils/           # chatbot_trainer
    │   └── data/            # career_paths.json, chatbot_intents.json, chatbot_model.pth
    └── management/commands/ # scrape_jobs, train_chatbot, train_career_model
```

## Getting started

### 1. Prerequisites

- Python 3.10 or newer
- PostgreSQL

### 2. Install dependencies

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install torch scikit-learn numpy
```

The ML libraries are not listed in `requirements.txt`. Without PyTorch and scikit-learn the API still starts, but the recommender and chatbot fall back to limited behaviour.

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql://<user>:<password>@localhost:5432/pathfinder-db
SECRET_KEY=<your-django-secret-key>
DEBUG=True
```

### 4. Set up the database

```bash
createdb pathfinder-db
python manage.py migrate
python manage.py createsuperuser
```

To use the admin-only endpoints, set the user's `role` to `ADMIN` (for example from the Django admin at `/admin/`).

### 5. Run the server

```bash
python manage.py runserver
```

The API is served at `http://localhost:8000/api/`. CORS is enabled for `http://localhost:3000`.

## Authentication

Get a token from `POST /api/auth/login/` and send it in the header of each request:

```
Authorization: Bearer <access_token>
```

Access tokens last 1 day and refresh tokens last 7 days.

## API endpoints

All routes are prefixed with `/api/`. Every endpoint needs a JWT unless it is marked as public.

### Auth

| Method | Endpoint | Description |
|---|---|---|
| POST | `auth/register/` | Register a new user (public) |
| POST | `auth/login/` | Get access and refresh tokens (public) |
| POST | `auth/refresh/` | Refresh the access token (public) |
| GET | `auth/getAllUsers/` | List all users, paginated (admin) |

### Profile

| Method | Endpoint | Description |
|---|---|---|
| POST | `profile/createProfile/` | Create the current user's profile |
| GET | `profile/getProfileByJWT/` | Get the current user's profile |
| PUT | `profile/updateProfile/` | Update the profile |
| POST | `profile/addEducationToProfile/` | Add an education entry |
| DELETE | `profile/deleteEducationFromProfile/<id>/` | Delete an education entry |
| POST | `profile/addExperienceToProfile/` | Add an experience entry |
| DELETE | `profile/deleteExperienceFromProfile/<id>/` | Delete an experience entry |

### Recommendations and career guidance

| Method | Endpoint | Description |
|---|---|---|
| GET | `recommendation/getCareerPaths/` | Career paths recommended from the user's profile |
| POST | `career/recommend/` | Recommend careers from `skills`, `interests` and `limit` |
| POST | `career/skill_gap/` | Skill gap for `career_title` |
| POST | `career/chatbot/` | Chat with the career bot using `message` (public) |
| GET | `career/careers/` | List all career paths |
| POST | `career/train_chatbot/` | Add training data or retrain the chatbot |
| POST | `career/train_model/` | Retrain the career recommender |

### Jobs

| Method | Endpoint | Description |
|---|---|---|
| GET | `jobs/` | List jobs. Filters: `search`, `location`, `job_type`, `source`, `skill` |
| GET | `jobs/<id>/` | Job details |
| GET | `jobs/relevant/` | Jobs relevant to the user's profile |
| POST | `jobs/scrape/` | Scrape LinkedIn using `keywords`, `location` and `limit` |
| POST | `jobs/recommend/` | ML-based job recommendations |

### Feedback

| Method | Endpoint | Description |
|---|---|---|
| POST | `feedback/create/` | Submit feedback (`subject`, `message`) |
| GET | `feedback/user/` | The current user's feedback |
| GET | `feedback/` | All feedback (admin) |
| PUT | `feedback/update/<id>/` | Update a feedback status to `PENDING`, `REVIEWED` or `RESOLVED` (admin) |

## Management commands

```bash
# Scrape jobs from LinkedIn
python manage.py scrape_jobs --keywords "python developer" --location "Lahore" --limit 25

# Chatbot training
python manage.py train_chatbot list
python manage.py train_chatbot add --message "How do I become a data scientist?" --intent career_advice
python manage.py train_chatbot create --tag <tag> --patterns '["..."]' --responses '["..."]'
python manage.py train_chatbot import --file intents.json
python manage.py train_chatbot retrain --epochs 50 --learning-rate 0.001

# Train the career recommendation model
python manage.py train_career_model
```

## Example requests

```bash
# Register
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "ali", "email": "ali@example.com", "password": "StrongPass123", "name": "Ali Khan", "role": "STUDENT"}'

# Ask the chatbot
curl -X POST http://localhost:8000/api/career/chatbot/ \
  -H "Content-Type: application/json" \
  -d '{"message": "What career should I pursue?"}'

# Career recommendations
curl -X POST http://localhost:8000/api/career/recommend/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"skills": ["Python", "SQL", "Machine Learning"], "limit": 5}'
```
