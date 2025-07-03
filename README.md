# AgriInsight - Plant Disease Detection System

A Django-based web application for detecting plant diseases using AI/ML technology.

## Features

- Plant disease detection using machine learning
- User authentication with Firebase
- Expert advice system
- Feedback and rating system
- E-commerce store for agricultural products
- Responsive design

## Tech Stack

- **Backend**: Django 5.2.3
- **Frontend**: HTML, CSS, JavaScript
- **Authentication**: Firebase Authentication
- **Database**: Firebase Realtime Database
- **Deployment**: Vercel

## Team Members

- **Dr. Sadia Ali** - Project Supervisor
- **Arbab Mehmood** - Website & AI Developer
- **Alisha Atta** - Designer & Co-Developer

## Vercel Deployment

This project is configured for deployment on Vercel. The following files are essential for Vercel deployment:

- `vercel.json` - Vercel configuration
- `requirements.txt` - Python dependencies
- `build_files.sh` - Build script
- `manage.py` - Django management script

### Deployment Steps

1. Push your code to GitHub
2. Connect your GitHub repository to Vercel
3. Vercel will automatically detect the Django configuration
4. Deploy!

## Local Development

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run migrations: `python manage.py migrate`
4. Start the server: `python manage.py runserver`

## Note

This is a frontend-only deployment. The ML model functionality is disabled for Vercel deployment due to size limitations. For full functionality including ML predictions, consider deploying on platforms like Heroku, Railway, or AWS. 
