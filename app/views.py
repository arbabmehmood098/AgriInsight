from django.core.checks import database
import pyrebase
from pyexpat.errors import messages
from django.shortcuts import render, redirect
from django.contrib import messages
import requests
import datetime
import os
import tensorflow as tf
import numpy as np
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.http import JsonResponse
import re
import json

Config = {
  "apiKey": "AIzaSyCF1p34L0V58UdJTRX9cNzI9DxrGQfHgnk",
  "authDomain": "agriinsight-cb999.firebaseapp.com",
  "databaseURL": "https://agriinsight-cb999-default-rtdb.firebaseio.com",
  "projectId": "agriinsight-cb999",
  "storageBucket": "agriinsight-cb999.firebasestorage.app",
  "messagingSenderId": "921501303356",
  "appId": "1:921501303356:web:1ca39c383fb84ff69eb939",
  "measurementId": "G-VYP9V6WPFJ"
}
firebase = pyrebase.initialize_app(Config)
auth = firebase.auth()
datbase = firebase.database()


def get_user_context(request):
    """Helper function to get user authentication context"""
    context = {
        'is_authenticated': False,
        'user': None
    }
    
    # Check if user is logged in via session
    uid = request.session.get('uid')
    
    if uid:
        # First try to get user data from session cache
        session_user_data = request.session.get('user_data')
        
        if session_user_data:
            context['is_authenticated'] = True
            context['user'] = session_user_data
        else:
            # Try to get user data from Firebase
            try:
                user_data = datbase.child("users").child(uid).get().val()
                
                if user_data:
                    context['is_authenticated'] = True
                    context['user'] = user_data
                    # Cache user data in session for future requests
                    request.session['user_data'] = user_data
                else:
                    # User exists in session but no data in database
                    # Create a basic user object with available info
                    fallback_user = {
                        'name': 'User',
                        'email': 'user@example.com',
                        'created_at': None,
                        'last_login': None,
                        'profile_complete': False,
                        'account_type': 'email'
                    }
                    context['is_authenticated'] = True
                    context['user'] = fallback_user
                    request.session['user_data'] = fallback_user
            except Exception as e:
                # If there's a database error, we can still show the user as logged in
                # but with limited information
                fallback_user = {
                    'name': 'User',
                    'email': 'user@example.com',
                    'created_at': None,
                    'last_login': None,
                    'profile_complete': False,
                    'account_type': 'email'
                }
                context['is_authenticated'] = True
                context['user'] = fallback_user
                request.session['user_data'] = fallback_user
        # Fetch user orders
        try:
            user_orders = datbase.child("users").child(uid).child("orders").get().val()
            if user_orders:
                # Convert to list and sort by ordered_at (latest first)
                orders_list = list(user_orders.values())
                orders_list.sort(key=lambda x: x.get('ordered_at', ''), reverse=True)
                context['user_orders'] = orders_list
            else:
                context['user_orders'] = []
        except Exception as e:
            context['user_orders'] = []
    
    return context


def home_view(request):
    context = get_user_context(request)
    return render(request, 'app/home.html', context)

def about(request):
    context = get_user_context(request)
    return render(request, 'app/about.html', context)

def model(request):
    context = get_user_context(request)
    return render(request, 'app/model.html', context)

def feedback(request):
    context = get_user_context(request)
    
    if request.method == 'POST':
        # Check if user is authenticated
        if not context['is_authenticated']:
            messages.error(request, 'Please login first to submit feedback.')
            return redirect('login')
        
        # Get form data
        name = request.POST.get('name')
        email = request.POST.get('email')
        rating = request.POST.get('rating')
        category = request.POST.get('category')
        message = request.POST.get('message')
        
        # Validate required fields
        if not all([name, email, rating, category, message]):
            messages.error(request, 'All fields are required.')
            return render(request, 'app/feedback.html', context)
        
        # Validate rating
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                raise ValueError("Invalid rating")
        except (ValueError, TypeError):
            messages.error(request, 'Please select a valid rating (1-5).')
            return render(request, 'app/feedback.html', context)
        
        # Get user UID from session
        uid = request.session.get('uid')
        
        try:
            # Get current timestamp
            current_time = datetime.datetime.now()
            
            # Prepare feedback data with formatted timestamps
            feedback_data = {
                "name": name,
                "email": email,
                "rating": rating,
                "category": category,
                "message": message,
                "submitted_at": {
                    ".sv": "timestamp"
                },
                "formatted_date": current_time.strftime("%B %d, %Y"),
                "formatted_time": current_time.strftime("%I:%M %p"),
                "day_name": current_time.strftime("%A"),
                "month_name": current_time.strftime("%B"),
                "year": current_time.year,
                "month": current_time.month,
                "day": current_time.day,
                "hour": current_time.hour,
                "minute": current_time.minute,
                "second": current_time.second,
                "user_uid": uid,
                "user_name": context['user'].get('name', 'Unknown'),
                "user_email": context['user'].get('email', 'Unknown')
            }
            
            # Store feedback under the user's data in Firebase
            feedback_result = datbase.child("users").child(uid).child("feedback").push(feedback_data)
            
            if feedback_result:
                messages.success(request, 'Thank you for your feedback! Your response has been recorded successfully.')
                return redirect('feedback')
            else:
                messages.error(request, 'Failed to save feedback. Please try again.')
                
        except Exception as e:
            print(f"Error saving feedback: {e}")
            messages.error(request, 'An error occurred while saving your feedback. Please try again.')
    
    return render(request, 'app/feedback.html', context)

def online_advise(request):
    context = get_user_context(request)
    
    if request.method == 'POST':
        # Check if user is authenticated
        if not context['is_authenticated']:
            messages.error(request, 'Please login first to submit an advice request.')
            return redirect('login')
        
        # Get form data
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone', '')
        plant_type = request.POST.get('plant_type')
        issue_type = request.POST.get('issue_type')
        description = request.POST.get('description')
        
        # Validate required fields
        required_fields = [name, email, plant_type, issue_type, description]
        if not all(required_fields):
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'app/online_advise.html', context)
        
        # Get user UID from session
        uid = request.session.get('uid')
        
        try:
            # Handle file uploads
            uploaded_files = []
            if 'images' in request.FILES:
                files = request.FILES.getlist('images')
                for file in files:
                    if file.size <= 5 * 1024 * 1024:  # 5MB limit
                        # For now, we'll store file info (in a real app, you'd upload to cloud storage)
                        uploaded_files.append({
                            'name': file.name,
                            'size': file.size,
                            'type': file.content_type
                        })
            
            # Get current timestamp
            current_time = datetime.datetime.now()
            
            # Prepare advice request data with formatted timestamps
            advice_data = {
                "name": name,
                "email": email,
                "phone": phone,
                "plant_type": plant_type,
                "issue_type": issue_type,
                "description": description,
                "uploaded_files": uploaded_files,
                "submitted_at": {
                    ".sv": "timestamp"
                },
                "formatted_date": current_time.strftime("%B %d, %Y"),
                "formatted_time": current_time.strftime("%I:%M %p"),
                "day_name": current_time.strftime("%A"),
                "month_name": current_time.strftime("%B"),
                "year": current_time.year,
                "month": current_time.month,
                "day": current_time.day,
                "hour": current_time.hour,
                "minute": current_time.minute,
                "second": current_time.second,
                "status": "pending",
                "user_uid": uid,
                "user_name": context['user'].get('name', 'Unknown'),
                "user_email": context['user'].get('email', 'Unknown')
            }
            
            # Store advice request under the user's data in Firebase
            advice_result = datbase.child("users").child(uid).child("advice_requests").push(advice_data)
            
            if advice_result:
                messages.success(request, 'Your advice request has been submitted successfully! Our experts will review your request and get back to you soon.')
                return redirect('online_advise')
            else:
                messages.error(request, 'Failed to submit advice request. Please try again.')
                
        except Exception as e:
            print(f"Error saving advice request: {e}")
            messages.error(request, 'An error occurred while submitting your request. Please try again.')
    
    return render(request, 'app/online_advise.html', context)


def signup(request):
    context = get_user_context(request)
    
    # If user is already logged in, redirect to home
    if context['is_authenticated']:
        return redirect('home')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        name = request.POST.get('name')

        # Validate required fields
        if not email or not password or not name:
            messages.error(request, 'All fields are required.')
            return render(request, 'app/signup.html', context)

        # Validate email format
        if '@' not in email or '.' not in email:
            messages.error(request, 'Please enter a valid email address.')
            return render(request, 'app/signup.html', context)

        # Validate password length
        if len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters long.')
            return render(request, 'app/signup.html', context)

        try:
            # Create user in Firebase Authentication
            user = auth.create_user_with_email_and_password(email, password)
            uid = user['localId']
            
            # Prepare user data for Firebase Realtime Database
            user_data = {
                "name": name,
                "email": email,
                "created_at": {
                    ".sv": "timestamp"
                },
                "last_login": {
                    ".sv": "timestamp"
                },
                "profile_complete": True,
                "account_type": "email"
            }
            
            # Save user data to Firebase Realtime Database
            try:
                print(f"Attempting to save user data to Firebase Database...")
                print(f"UID: {uid}")
                print(f"User data: {user_data}")
                
                # Try to write to database
                result = datbase.child("users").child(uid).set(user_data)
                print(f"Database write result: {result}")
                print(f"User data saved to Firebase Database for UID: {uid}")
                
                # Store complete user data in session
                session_user_data = {
                    "name": name,
                    "email": email,
                    "created_at": None,  # Will be set by Firebase
                    "last_login": None,  # Will be set by Firebase
                    "profile_complete": True,
                    "account_type": "email"
                }
                request.session['user_data'] = session_user_data
                
            except Exception as db_error:
                print(f"Database write error details:")
                print(f"Error type: {type(db_error)}")
                print(f"Error message: {str(db_error)}")
                print(f"Error args: {db_error.args}")
                
                # Try alternative approach - use push() instead of set()
                try:
                    print("Trying alternative database write method...")
                    result = datbase.child("users").child(uid).push(user_data)
                    print(f"Alternative write result: {result}")
                except Exception as alt_error:
                    print(f"Alternative write also failed: {alt_error}")
                
                # If database write fails, we still have the user created in auth
                # Create fallback user data for session
                fallback_user_data = {
                    "name": name,
                    "email": email,
                    "created_at": None,
                    "last_login": None,
                    "profile_complete": False,
                    "account_type": "email"
                }
                request.session['user_data'] = fallback_user_data
                messages.warning(request, 'Account created but profile data could not be saved. You can update your profile later.')
            
            # Log the user in
            request.session['uid'] = str(uid)
            
            messages.success(request, 'Account created successfully! Welcome to AgriInsight!')
            return redirect('home')

        except Exception as e:
            error_message = str(e)
            print(f"Signup error: {error_message}")  # For debugging
            
            if "EMAIL_EXISTS" in error_message:
                messages.error(request, 'An account with this email already exists. Please use a different email or try logging in.')
            elif "WEAK_PASSWORD" in error_message:
                messages.error(request, 'Password is too weak. Please use a stronger password (at least 6 characters).')
            elif "INVALID_EMAIL" in error_message:
                messages.error(request, 'Please enter a valid email address.')
            elif "NETWORK_ERROR" in error_message or "TIMEOUT" in error_message:
                messages.error(request, 'Network error. Please check your internet connection and try again.')
            elif "QUOTA_EXCEEDED" in error_message:
                messages.error(request, 'Service temporarily unavailable. Please try again later.')
            elif "Permission denied" in error_message:
                messages.error(request, 'Database permission error. Please contact support.')
            else:
                messages.error(request, f'An error occurred during signup: {error_message}')

    return render(request, 'app/signup.html', context)


def login(request):
    context = get_user_context(request)
    # If user is already logged in, redirect to home
    if context['is_authenticated']:
        return redirect('home')
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        try:
            # Sign in user with Firebase
            user = auth.sign_in_with_email_and_password(email, password)
            uid = user['localId']
            # Try to get user data from Firebase Database and update last_login
            try:
                user_data = datbase.child("users").child(uid).get().val()
                if user_data:
                    # Update last_login timestamp
                    datbase.child("users").child(uid).update({
                        "last_login": {
                            ".sv": "timestamp"
                        }
                    })
                    print(f"Last login updated for UID: {uid}")
                    # Store user data in session
                    request.session['user_data'] = user_data
                else:
                    # Create user data in the database if it doesn't exist
                    new_user_data = {
                        'name': 'User',
                        'email': email,
                        'created_at': {".sv": "timestamp"},
                        'last_login': {".sv": "timestamp"},
                        'profile_complete': False,
                        'account_type': 'email'
                    }
                    datbase.child("users").child(uid).set(new_user_data)
                    request.session['user_data'] = new_user_data
            except Exception as e:
                print(f"Database read/update error during login: {e}")
                # Try to create user data in the database if error occurs
                try:
                    new_user_data = {
                        'name': 'User',
                        'email': email,
                        'created_at': {".sv": "timestamp"},
                        'last_login': {".sv": "timestamp"},
                        'profile_complete': False,
                        'account_type': 'email'
                    }
                    datbase.child("users").child(uid).set(new_user_data)
                    request.session['user_data'] = new_user_data
                except Exception as inner_e:
                    print(f"Failed to create user data in database: {inner_e}")
                    fallback_user = {
                        'name': 'User',
                        'email': email,
                        'created_at': None,
                        'last_login': None,
                        'profile_complete': False,
                        'account_type': 'email'
                    }
                    request.session['user_data'] = fallback_user
            # Store user session
            request.session['uid'] = str(uid)
            messages.success(request, 'Logged in successfully!')
            return redirect('home')
        except Exception as e:
            error_message = str(e)
            print(f"LOGIN ERROR DEBUG: {error_message}")  # Debug print
            # Try to extract error code from Firebase error JSON if present
            error_code = None
            # Try to extract error code from JSON in the error message
            match = re.search(r'\{.*\}', error_message)
            if match:
                try:
                    error_json = json.loads(match.group())
                    if 'error' in error_json and 'message' in error_json['error']:
                        error_code = error_json['error']['message']
                except Exception as json_e:
                    print(f"Error parsing Firebase error JSON: {json_e}")
            # Fallback to string matching
            if error_code in ["INVALID_PASSWORD", "INVALID_LOGIN_CREDENTIALS"] or ("INVALID_PASSWORD" in error_message or "INVALID_LOGIN_CREDENTIALS" in error_message or "password is invalid" in error_message.lower()):
                messages.error(request, 'Invalid email or password.')
            else:
                messages.error(request, f'An error occurred during login. Please try again. ({error_message})')
    return render(request, 'app/login.html', context)


def logout(request):
    # Clear all user session data
    request.session.pop('uid', None)
    request.session.pop('user_data', None)
    messages.success(request, 'Logged out successfully!')
    return redirect('home')


def blogpost(request):
    context = get_user_context(request)
    return render(request, 'app/blogpost.html', context)


def debug_users(request):
    """Debug view to check users in Firebase Database"""
    try:
        print("Testing Firebase Database connection...")
        
        # Test basic database access
        try:
            test_data = datbase.child("test").get().val()
            print(f"Test read successful: {test_data}")
        except Exception as test_error:
            print(f"Test read failed: {test_error}")
        
        # Get all users from Firebase Database
        print("Attempting to read users from database...")
        users = datbase.child("users").get().val()
        print(f"Users data: {users}")
        
        if users:
            user_list = []
            for uid, user_data in users.items():
                user_list.append({
                    'uid': uid,
                    'name': user_data.get('name', 'Unknown'),
                    'email': user_data.get('email', 'No email'),
                    'created_at': user_data.get('created_at', 'Not set'),
                    'last_login': user_data.get('last_login', 'Not set'),
                    'profile_complete': user_data.get('profile_complete', False),
                    'account_type': user_data.get('account_type', 'Unknown')
                })
            
            context = {
                'users': user_list,
                'total_users': len(user_list),
                'database_status': 'Connected'
            }
        else:
            context = {
                'users': [],
                'total_users': 0,
                'database_status': 'Connected but no users found'
            }
            
    except Exception as e:
        print(f"Debug users error: {e}")
        context = {
            'users': [],
            'total_users': 0,
            'database_status': f'Error: {str(e)}'
        }
    
    return render(request, 'app/debug_users.html', context)


def test_database(request):
    """Test Firebase Database connectivity and permissions"""
    test_results = []
    
    try:
        # Test 1: Basic read
        try:
            test_read = datbase.child("test").get().val()
            test_results.append({
                'test': 'Basic Read',
                'status': 'Success',
                'result': str(test_read)
            })
        except Exception as e:
            test_results.append({
                'test': 'Basic Read',
                'status': 'Failed',
                'result': str(e)
            })
        
        # Test 2: Write test data
        try:
            test_data = {
                "test": True,
                "timestamp": {
                    ".sv": "timestamp"
                },
                "message": "Database test"
            }
            write_result = datbase.child("test").child("write_test").set(test_data)
            test_results.append({
                'test': 'Write Test',
                'status': 'Success',
                'result': str(write_result)
            })
        except Exception as e:
            test_results.append({
                'test': 'Write Test',
                'status': 'Failed',
                'result': str(e)
            })
        
        # Test 3: Read users
        try:
            users = datbase.child("users").get().val()
            test_results.append({
                'test': 'Read Users',
                'status': 'Success',
                'result': f"Found {len(users) if users else 0} users"
            })
        except Exception as e:
            test_results.append({
                'test': 'Read Users',
                'status': 'Failed',
                'result': str(e)
            })
        
        # Test 4: Write user test
        try:
            test_user = {
                "name": "Test User",
                "email": "test@example.com",
                "test": True,
                "timestamp": {
                    ".sv": "timestamp"
                }
            }
            user_write = datbase.child("users").child("test_user").set(test_user)
            test_results.append({
                'test': 'Write User',
                'status': 'Success',
                'result': str(user_write)
            })
        except Exception as e:
            test_results.append({
                'test': 'Write User',
                'status': 'Failed',
                'result': str(e)
            })
        
        context = {
            'test_results': test_results,
            'database_url': Config['databaseURL'],
            'project_id': Config['projectId']
        }
        
    except Exception as e:
        test_results.append({
            'test': 'General',
            'status': 'Failed',
            'result': str(e)
        })
        context = {
            'test_results': test_results,
            'database_url': Config['databaseURL'],
            'project_id': Config['projectId']
        }
    
    return render(request, 'app/test_database.html', context)


def user_feedback_history(request):
    """Display feedback history for the logged-in user"""
    context = get_user_context(request)
    
    # Check if user is authenticated
    if not context['is_authenticated']:
        messages.error(request, 'Please login to view your feedback history.')
        return redirect('login')
    
    uid = request.session.get('uid')
    
    try:
        # Get user's feedback from Firebase
        user_feedback = datbase.child("users").child(uid).child("feedback").get().val()
        
        if user_feedback:
            # Convert Firebase data to list format
            feedback_list = []
            for feedback_id, feedback_data in user_feedback.items():
                feedback_list.append({
                    'id': feedback_id,
                    'name': feedback_data.get('name', 'Unknown'),
                    'email': feedback_data.get('email', 'Unknown'),
                    'rating': feedback_data.get('rating', 0),
                    'category': feedback_data.get('category', 'Unknown'),
                    'message': feedback_data.get('message', ''),
                    'submitted_at': feedback_data.get('submitted_at', 'Unknown'),
                    'formatted_date': feedback_data.get('formatted_date', 'Unknown'),
                    'formatted_time': feedback_data.get('formatted_time', 'Unknown'),
                    'day_name': feedback_data.get('day_name', 'Unknown'),
                    'user_name': feedback_data.get('user_name', 'Unknown'),
                    'user_email': feedback_data.get('user_email', 'Unknown')
                })
            
            # Sort by submission date (newest first)
            feedback_list.sort(key=lambda x: x['submitted_at'], reverse=True)
            
            context['feedback_list'] = feedback_list
            context['total_feedback'] = len(feedback_list)
        else:
            context['feedback_list'] = []
            context['total_feedback'] = 0
            
    except Exception as e:
        print(f"Error fetching feedback history: {e}")
        context['feedback_list'] = []
        context['total_feedback'] = 0
        messages.error(request, 'Failed to load feedback history. Please try again.')
    
    return render(request, 'app/feedback_history.html', context)


def admin_feedback_view(request):
    """Admin view to see all feedback from all users"""
    context = get_user_context(request)
    
    # Check if user is authenticated (basic admin check)
    if not context['is_authenticated']:
        messages.error(request, 'Please login to access admin features.')
        return redirect('login')
    
    try:
        # Get all users from Firebase
        all_users = datbase.child("users").get().val()
        
        all_feedback = []
        total_feedback_count = 0
        
        if all_users:
            for uid, user_data in all_users.items():
                user_feedback = user_data.get('feedback', {})
                
                if user_feedback:
                    for feedback_id, feedback_data in user_feedback.items():
                        all_feedback.append({
                            'id': feedback_id,
                            'user_uid': uid,
                            'user_name': user_data.get('name', 'Unknown'),
                            'user_email': user_data.get('email', 'Unknown'),
                            'feedback_name': feedback_data.get('name', 'Unknown'),
                            'feedback_email': feedback_data.get('email', 'Unknown'),
                            'rating': feedback_data.get('rating', 0),
                            'category': feedback_data.get('category', 'Unknown'),
                            'message': feedback_data.get('message', ''),
                            'submitted_at': feedback_data.get('submitted_at', 'Unknown'),
                            'formatted_date': feedback_data.get('formatted_date', 'Unknown'),
                            'formatted_time': feedback_data.get('formatted_time', 'Unknown'),
                            'day_name': feedback_data.get('day_name', 'Unknown')
                        })
                        total_feedback_count += 1
        
        # Sort by submission date (newest first)
        all_feedback.sort(key=lambda x: x['submitted_at'], reverse=True)
        
        context['all_feedback'] = all_feedback
        context['total_feedback_count'] = total_feedback_count
        context['total_users'] = len(all_users) if all_users else 0
        
    except Exception as e:
        print(f"Error fetching admin feedback: {e}")
        context['all_feedback'] = []
        context['total_feedback_count'] = 0
        context['total_users'] = 0
        messages.error(request, 'Failed to load feedback data. Please try again.')
    
    return render(request, 'app/admin_feedback.html', context)


def user_advice_history(request):
    """Display advice request history for the logged-in user"""
    context = get_user_context(request)
    
    # Check if user is authenticated
    if not context['is_authenticated']:
        messages.error(request, 'Please login to view your advice request history.')
        return redirect('login')
    
    uid = request.session.get('uid')
    
    try:
        # Get user's advice requests from Firebase
        user_advice = datbase.child("users").child(uid).child("advice_requests").get().val()
        
        if user_advice:
            # Convert Firebase data to list format
            advice_list = []
            for advice_id, advice_data in user_advice.items():
                advice_list.append({
                    'id': advice_id,
                    'name': advice_data.get('name', 'Unknown'),
                    'email': advice_data.get('email', 'Unknown'),
                    'phone': advice_data.get('phone', ''),
                    'plant_type': advice_data.get('plant_type', 'Unknown'),
                    'issue_type': advice_data.get('issue_type', 'Unknown'),
                    'description': advice_data.get('description', ''),
                    'status': advice_data.get('status', 'pending'),
                    'uploaded_files': advice_data.get('uploaded_files', []),
                    'submitted_at': advice_data.get('submitted_at', 'Unknown'),
                    'formatted_date': advice_data.get('formatted_date', 'Unknown'),
                    'formatted_time': advice_data.get('formatted_time', 'Unknown'),
                    'day_name': advice_data.get('day_name', 'Unknown'),
                    'user_name': advice_data.get('user_name', 'Unknown'),
                    'user_email': advice_data.get('user_email', 'Unknown')
                })
            
            # Sort by submission date (newest first)
            advice_list.sort(key=lambda x: x['submitted_at'], reverse=True)
            
            context['advice_list'] = advice_list
            context['total_advice'] = len(advice_list)
        else:
            context['advice_list'] = []
            context['total_advice'] = 0
            
    except Exception as e:
        print(f"Error fetching advice history: {e}")
        context['advice_list'] = []
        context['total_advice'] = 0
        messages.error(request, 'Failed to load advice request history. Please try again.')
    
    return render(request, 'app/advice_history.html', context)


def predict_plant_disease(request):
    context = get_user_context(request)
    prediction_result = None
    error_message = None
    class_name = [
        'Apple___Apple_scab', 'Apple___Black_rot', 'Apple___Cedar_apple_rust', 'Apple___healthy',
        'Blueberry___healthy', 'Cherry_(including_sour)___Powdery_mildew', 'Cherry_(including_sour)___healthy',
        'Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot', 'Corn_(maize)___Common_rust_',
        'Corn_(maize)___Northern_Leaf_Blight', 'Corn_(maize)___healthy', 'Grape___Black_rot',
        'Grape___Esca_(Black_Measles)', 'Grape___Leaf_blight_(Isariopsis_Leaf_Spot)', 'Grape___healthy',
        'Orange___Haunglongbing_(Citrus_greening)', 'Peach___Bacterial_spot', 'Peach___healthy',
        'Pepper,_bell___Bacterial_spot', 'Pepper,_bell___healthy', 'Potato___Early_blight',
        'Potato___Late_blight', 'Potato___healthy', 'Raspberry___healthy', 'Soybean___healthy',
        'Squash___Powdery_mildew', 'Strawberry___Leaf_scorch', 'Strawberry___healthy',
        'Tomato___Bacterial_spot', 'Tomato___Early_blight', 'Tomato___Late_blight', 'Tomato___Leaf_Mold',
        'Tomato___Septoria_leaf_spot', 'Tomato___Spider_mites Two-spotted_spider_mite', 'Tomato___Target_Spot',
        'Tomato___Tomato_Yellow_Leaf_Curl_Virus', 'Tomato___Tomato_mosaic_virus', 'Tomato___healthy'
    ]

    # Limit for non-logged-in users
    if not context['is_authenticated']:
        predictions_left = request.session.get('predictions_left', 5)
        context['predictions_left'] = predictions_left
        if predictions_left <= 0:
            context['error_message'] = 'You have reached the maximum of 5 predictions. Please log in to continue unlimited predictions.'
            return render(request, 'app/model.html', context)

    if request.method == 'POST' and request.FILES.get('image'):
        image_file = request.FILES['image']
        try:
            # Save the uploaded image temporarily
            temp_image_path = default_storage.save('temp/' + image_file.name, ContentFile(image_file.read()))
            temp_image_full_path = os.path.join(settings.MEDIA_ROOT, temp_image_path) if hasattr(settings, 'MEDIA_ROOT') else temp_image_path

            # Load the model (use .h5 extension)
            model_path = os.path.join(settings.BASE_DIR, 'Backend', 'trained_model.h5')
            model = tf.keras.models.load_model(model_path)

            # Preprocess the image
            image = tf.keras.preprocessing.image.load_img(temp_image_full_path, target_size=(128, 128))
            input_arr = tf.keras.preprocessing.image.img_to_array(image)
            input_arr = np.array([input_arr])  # Convert single image to a batch
            prediction = model.predict(input_arr)
            result_index = np.argmax(prediction)
            predicted_class = class_name[result_index]
            confidence = float(np.max(tf.nn.softmax(prediction)))
            prediction_result = {
                'class': predicted_class,
                'confidence': f'{confidence*100:.2f}%'
            }
            # Clean up temp file
            default_storage.delete(temp_image_path)

            # Store prediction details for logged-in users
            if context['is_authenticated']:
                uid = request.session.get('uid')
                prediction_data = {
                    'predicted_class': predicted_class,
                    'confidence': f'{confidence*100:.2f}%',
                    'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                try:
                    datbase.child('users').child(uid).child('predictions').push(prediction_data)
                except Exception as e:
                    print(f"Error saving prediction: {e}")
            else:
                # Decrement predictions left for non-logged-in users
                predictions_left = request.session.get('predictions_left', 5)
                predictions_left -= 1
                request.session['predictions_left'] = predictions_left
                context['predictions_left'] = predictions_left

        except Exception as e:
            error_message = f'Prediction failed: {str(e)}'
            print(error_message)
    context['prediction_result'] = prediction_result
    context['error_message'] = error_message
    return render(request, 'app/model.html', context)


def profile(request):
    context = get_user_context(request)
    if not context['is_authenticated']:
        messages.error(request, 'Please login to view your profile.')
        return redirect('login')
    # Add joined date to context if available
    user_data = context.get('user', {})
    joined_date = None
    created_at = user_data.get('created_at')
    if created_at:
        # If it's a timestamp (int/float), convert to readable date
        try:
            if isinstance(created_at, (int, float)):
                joined_date = datetime.datetime.fromtimestamp(created_at/1000).strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(created_at, str) and created_at.isdigit():
                joined_date = datetime.datetime.fromtimestamp(int(created_at)/1000).strftime('%Y-%m-%d %H:%M:%S')
            else:
                joined_date = str(created_at)
        except Exception:
            joined_date = str(created_at)
    context['joined_date'] = joined_date
    return render(request, 'app/profile.html', context)


def workings(request):
    context = get_user_context(request)
    return render(request, 'app/workings.html', context)


def store(request):
    context = get_user_context(request)
    products = [
        {"id": 1, "name": "BioNeem Plant Pesticide", "description": "Organic neem-based pesticide for all crops.", "price": 1200},
        {"id": 2, "name": "Fungikill Plus", "description": "Broad-spectrum fungicide for vegetables.", "price": 950},
        {"id": 3, "name": "InsectGuard 500ml", "description": "Effective against aphids and whiteflies.", "price": 800},
        {"id": 4, "name": "CropSafe Herbal Spray", "description": "Safe for fruit and vegetable plants.", "price": 1100},
        {"id": 5, "name": "RootShield Granules", "description": "Protects roots from soil-borne pests.", "price": 1500},
        {"id": 6, "name": "GreenLeaf Defender", "description": "Systemic pesticide for leaf-eating insects.", "price": 1050},
        {"id": 7, "name": "EcoGrow Pyrethrum Spray", "description": "Natural pyrethrum-based spray for organic farming.", "price": 1350},
        {"id": 8, "name": "BlightBuster", "description": "Specialized for potato and tomato blight control.", "price": 1250},
        {"id": 9, "name": "MiteAway Oil", "description": "Controls mites and soft-bodied insects on fruits.", "price": 900},
        {"id": 10, "name": "SoilGuard Pro", "description": "Granular pesticide for soil pest management.", "price": 1600},
        {"id": 11, "name": "FruitCare Plus", "description": "Protects fruit crops from fungal and bacterial diseases.", "price": 1400},
        {"id": 12, "name": "VitaSpray Plant Tonic", "description": "Boosts plant immunity and pest resistance.", "price": 1150},
    ]
    context['products'] = products
    context['order_success'] = False
    context['cart'] = request.session.get('cart', {})
    context['cart_items'] = []
    context['cart_total'] = 0
    context['address_required'] = False
    context['address'] = ''
    context['address_error'] = ''
    context['order_error'] = ''
    context['cash_on_delivery_error'] = ''

    # Build cart items and total
    if context['cart']:
        for pid, qty in context['cart'].items():
            prod = next((p for p in products if str(p['id']) == str(pid)), None)
            if prod:
                item = prod.copy()
                item['quantity'] = qty
                item['total'] = qty * prod['price']
                context['cart_items'].append(item)
                context['cart_total'] += item['total']

    # Handle add to cart (AJAX or POST)
    if request.method == 'POST' and request.POST.get('action') == 'add_to_cart' and context['is_authenticated']:
        pid = request.POST.get('product_id')
        cart = request.session.get('cart', {})
        cart[pid] = cart.get(pid, 0) + 1
        request.session['cart'] = cart
        return JsonResponse({'success': True, 'cart_count': sum(cart.values())})

    # Handle remove from cart
    if request.method == 'POST' and request.POST.get('action') == 'remove_from_cart' and context['is_authenticated']:
        pid = request.POST.get('product_id')
        cart = request.session.get('cart', {})
        if pid in cart:
            del cart[pid]
            request.session['cart'] = cart
        return JsonResponse({'success': True, 'cart_count': sum(cart.values())})

    # Handle order placement
    if request.method == 'POST' and request.POST.get('action') == 'place_order' and context['is_authenticated']:
        uid = request.session.get('uid')
        cart = request.session.get('cart', {})
        if not cart:
            context['order_error'] = 'Your cart is empty.'
        else:
            # Cash on delivery check
            if not request.POST.get('cash_on_delivery'):
                context['cash_on_delivery_error'] = 'You must check Cash on Delivery to place your order.'
                context['address_required'] = False
            else:
                address = request.POST.get('address', '').strip()
                if not address:
                    context['address_required'] = True
                    context['address_error'] = 'Address is required to place an order.'
                else:
                    # Prepare order (do not save address to user profile)
                    order_items = []
                    total_bill = 0
                    for pid, qty in cart.items():
                        prod = next((p for p in products if str(p['id']) == str(pid)), None)
                        if prod:
                            order_items.append({
                                'product_id': prod['id'],
                                'product_name': prod['name'],
                                'price': prod['price'],
                                'quantity': qty,
                                'total': prod['price'] * qty
                            })
                            total_bill += prod['price'] * qty
                    order_data = {
                        'items': order_items,
                        'total_products': sum(cart.values()),
                        'total_bill': total_bill,
                        'address': address,
                        'ordered_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    try:
                        datbase.child('users').child(uid).child('orders').push(order_data)
                        context['order_success'] = True
                        request.session['cart'] = {}  # Clear cart
                        context['cart'] = {}
                        context['cart_items'] = []
                        context['cart_total'] = 0
                    except Exception as e:
                        context['order_error'] = str(e)
    return render(request, 'app/store.html', context)


def my_orders(request):
    context = get_user_context(request)
    if not context['is_authenticated']:
        messages.error(request, 'Please login to view your orders.')
        return redirect('login')
    uid = request.session.get('uid')
    orders = []
    try:
        user_orders = datbase.child('users').child(uid).child('orders').get().val()
        if user_orders:
            for order_id, order_data in user_orders.items():
                # Only include orders with a valid address, at least one item with a product name, and a total bill > 0
                items = order_data.get('items', [])
                has_valid_items = any(item.get('product_name') and item.get('total', 0) > 0 for item in items)
                if order_data.get('address') and has_valid_items and order_data.get('total_bill', 0) > 0:
                    status = order_data.get('status', 'pending')
                    order_data['status'] = status
                    order_data['id'] = order_id
                    orders.append(order_data)
            # Show most recent first
            orders.sort(key=lambda x: x.get('ordered_at', ''), reverse=True)
    except Exception as e:
        context['orders_error'] = str(e)
    context['orders'] = orders
    return render(request, 'app/my_orders.html', context)



