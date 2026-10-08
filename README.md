# Quizly Backend

![Python](https://img.shields.io/badge/python-3.14-blue)
![Django](https://img.shields.io/badge/django-6.1-092E20)
![DRF](https://img.shields.io/badge/DRF-3.18-A30000)
![License](https://img.shields.io/badge/license-educational-lightgrey)

A Django REST Framework backend for Quizly, an AI-powered quiz application. It creates quizzes from YouTube videos by extracting the audio, transcribing it with Whisper, and generating ten questions with Gemini.

## Frontend

The matching frontend is available in a separate repository:

[Quizly Frontend](https://github.com/Developer-Akademie-Backendkurs/project.Quizly)

## Contents

- [Frontend](#frontend)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Authentication](#authentication)
- [API Overview](#api-overview)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Notes for Local Development](#notes-for-local-development)

## Features

- User registration, login, token refresh, and logout
- JWT authentication with HTTP-only cookies
- Quiz generation from supported YouTube video URLs
- MP3 audio extraction with yt-dlp and FFmpeg
- Audio transcription with OpenAI Whisper
- Structured quiz generation with Gemini Flash
- Ten questions with four distinct answer options each
- Quiz listing, detail view, editing, and deletion
- Owner-based access control for stored quizzes
- Django admin support for quizzes and questions
- Interactive Swagger API documentation

## Tech Stack

| | |
|---|---|
| Language | Python 3.14 |
| Framework | Django 6.1 |
| API | Django REST Framework 3.18 |
| Authentication | JWT with HTTP-only cookies |
| Database | SQLite (local development) |
| AI generation | Google Gemini Flash |
| Transcription | OpenAI Whisper |
| Audio processing | yt-dlp and FFmpeg |
| API documentation | drf-yasg / Swagger |
| Testing | pytest, pytest-django, pytest-cov |

## Project Structure

```text
backend/
├── accounts_app/       registration, login, token refresh, and logout
│   ├── api/            serializers, views, URLs, and API documentation
│   └── tests/          authentication endpoint tests
├── quiz_app/           quizzes, questions, and generation pipeline
│   ├── api/            serializers, views, permissions, URLs, and documentation
│   ├── services/       audio download, transcription, and quiz generation
│   └── tests/          model, service, and endpoint tests
├── core/               project settings, root URLs, and API information
├── manage.py
├── requirements.txt
└── schema.yml          generated OpenAPI schema
```

## Getting Started

Quick version, if you just want to get it running on Windows:

```powershell
git clone https://github.com/JensBaumannDev/Quizly.git
cd Quizly
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py runserver
```

The API is then available at `http://127.0.0.1:8000/api/`.

### Step by step

**1. Clone the repository**

```bash
git clone https://github.com/JensBaumannDev/Quizly.git
cd Quizly
```

**2. Create and activate a virtual environment**

```bash
python -m venv .venv
```

| OS | Command |
|---|---|
| Windows PowerShell | `.\.venv\Scripts\Activate.ps1` |
| Windows Command Prompt | `.venv\Scripts\activate.bat` |
| macOS/Linux | `source .venv/bin/activate` |

**3. Install FFmpeg globally**

FFmpeg is required by yt-dlp to convert downloaded YouTube audio to MP3. On Windows it can be installed with:

```powershell
winget install --id Gyan.FFmpeg -e --source winget
```

Restart the terminal after the installation and verify that FFmpeg is available:

```bash
ffmpeg -version
```

**4. Install the Python dependencies**

```bash
pip install -r requirements.txt
```

**5. Set up environment variables**

Copy `.env.example` to `.env`:

```powershell
Copy-Item .env.example .env
```

Add your own Django secret key and Gemini API key:

```env
SECRET_KEY='YOUR_DJANGO_SECRET_KEY'
GEMINI_API_KEY='YOUR_GEMINI_API_KEY'
```

A Django secret key can be generated with:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**6. Apply migrations**

```bash
python manage.py migrate
```

**7. Create a superuser (optional)**

```bash
python manage.py createsuperuser
```

**8. Run the development server**

```bash
python manage.py runserver
```

## Authentication

Quizly uses JSON Web Tokens stored in HTTP-only cookies. A successful login sets an `access_token` and a `refresh_token`. The browser sends these cookies automatically when frontend requests use credentials.

- The access token authenticates protected API requests.
- The refresh token creates a new access token through `/api/token/refresh/`.
- Logout blacklists the refresh token and removes both cookies.

## API Overview

**Authentication**

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/register/` | Create a user account |
| POST | `/api/login/` | Log in and set JWT cookies |
| POST | `/api/token/refresh/` | Refresh the access token |
| POST | `/api/logout/` | Log out and clear JWT cookies |

**Quizzes**

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/quizzes/` | List the authenticated user's quizzes |
| POST | `/api/quizzes/` | Generate a quiz from a YouTube video |
| GET | `/api/quizzes/<id>/` | Retrieve an owned quiz |
| PATCH | `/api/quizzes/<id>/` | Update an owned quiz |
| DELETE | `/api/quizzes/<id>/` | Delete an owned quiz |

## API Documentation

With the development server running, the API documentation is available at:

- Swagger UI: `http://127.0.0.1:8000/swagger/`
- YAML schema: `http://127.0.0.1:8000/swagger.yaml`
- Static schema: `schema.yml`

Regenerate the static schema after changing an endpoint:

```bash
python manage.py generate_swagger schema.yml --format yaml --overwrite
```

## Testing

Run the complete test suite from the backend directory:

```bash
pytest
```

The pytest configuration automatically generates a terminal coverage report for `accounts_app` and `quiz_app`.

## Notes for Local Development

- The database file `db.sqlite3` is not tracked. Running the migrations creates a fresh local database.
- The `.env` file is not tracked. Never commit the Django secret key or Gemini API key.
- FFmpeg must be installed globally and available through the system path.
- The Whisper `base` model is downloaded automatically the first time a quiz is generated and is then cached locally.
- Quiz generation requires an active internet connection for YouTube downloads and Gemini requests.
- Gemini or YouTube may temporarily reject or limit external requests.
- The local frontend origin is configured as `http://127.0.0.1:5500`.
- Frontend requests must include credentials so the browser sends the JWT cookies.
- Django admin is available at `http://127.0.0.1:8000/admin/` after creating a superuser.
