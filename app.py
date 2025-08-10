from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import requests
import pandas as pd
import joblib
import json
import urllib.request
from model import train
from csv import DictWriter
import traceback
import sys
import os

# Load environment variables from a .env file
load_dotenv()

# Firebase and Firestore imports
import firebase_admin
from firebase_admin import credentials, firestore

# Global variables for firebase are provided in the environment
# We'll initialize the app and database connection here
db = None
try:
    if not firebase_admin._apps:
        # Load firebase config from a local JSON file instead of environment variable
        with open('firebase_config.json') as f:
            firebase_config = json.load(f)
        cred = credentials.Certificate(firebase_config)
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("Firestore client initialized successfully.")
except Exception as e:
    print(f"Error initializing Firestore: {e}")
    db = None

# Load the machine learning model once at the start
model = None
try:
    model = joblib.load('insta_model.joblib')
    print("Model loaded successfully")
except Exception as e:
    print(f"Error loading model: {e}")

app = Flask(__name__)
# The secret key is needed for session management in Flask-Login
app.secret_key = os.environ.get('SECRET_KEY') or 'a-very-secret-key-that-you-should-change'

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'signin'

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id):
        self.id = id
        self.email = None

    def get_id(self):
        return self.id

    @staticmethod
    def get(user_id):
        if not db:
            print("Database not initialized.")
            return None
        # Fetch user from Firestore by ID
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()
        if user_doc.exists:
            user_data = user_doc.to_dict()
            user = User(user_id)
            user.email = user_data['email']
            return user
        return None

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

new_data = {}

@app.route('/')
@login_required
def index():
    try:
        is_authenticated = current_user.is_authenticated
        return render_template('index.html', is_authenticated=is_authenticated)
    except Exception as e:
        print(f"Error in index route: {e}")
        return f"Error: {str(e)}", 500

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if not db:
        return "Database not initialized. Cannot sign up.", 500
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            return render_template('signup.html', error="Email and password are required.")

        # Check if user already exists
        users_ref = db.collection('users')
        query = users_ref.where('email', '==', email).limit(1).get()
        if query:
            return render_template('signup.html', error="An account with this email already exists.")

        # Hash the password for security
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        try:
            # Create a new user document in Firestore
            new_user_data = {
                'email': email,
                'password_hash': hashed_password
            }
            db.collection('users').add(new_user_data)
            return redirect(url_for('signin'))
        except Exception as e:
            print(f"Error during sign up: {e}")
            traceback.print_exc()
            return render_template('signup.html', error=f"An error occurred: {str(e)}")

    return render_template('signup.html')


@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if not db:
        print("Database not initialized. Cannot sign in.")
        return "Database not initialized. Cannot sign in.", 500
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        print(f"Signin attempt: email={email}")

        if not email or not password:
            print("Email or password missing.")
            return render_template('signin.html', error="Email and password are required.")

        try:
            # Fetch user from Firestore
            users_ref = db.collection('users')
            query = users_ref.where('email', '==', email).limit(1).get()
            print(f"Firestore query result: {query}")

            if not query:
                print("No user found with that email.")
                return render_template('signin.html', error="Invalid email or password.")

            user_doc = query[0]
            user_data = user_doc.to_dict()
            user_id = user_doc.id

            print(f"User found: {user_data}")

            # Check the password
            if check_password_hash(user_data['password_hash'], password):
                user = User(user_id)
                login_user(user)
                print("Login successful.")
                return redirect(url_for('index'))
            else:
                print("Password check failed.")
                return render_template('signin.html', error="Invalid email or password.")
        except Exception as e:
            print(f"Error during signin: {e}")
            traceback.print_exc()
            return render_template('signin.html', error=f"An unexpected error occurred: {str(e)}")

    return render_template('signin.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/predict', methods=['POST'])
@login_required
def predict():
    if not db:
        return "Database not initialized. Cannot perform prediction.", 500
    global new_data
    try:
        # ... (rest of your existing /predict route code) ...
        print("Entered /predict route")
        username = request.form.get('username')
        print(f"Received username: {username}")

        if not username:
            return jsonify({'success': False, 'error': 'Username is required!'}), 400

        # Use an environment variable for the key to keep it secure
        rapidapi_key = os.environ.get('RAPIDAPI_KEY')
        if not rapidapi_key:
            return jsonify({'success': False, 'error': 'API key not configured on the server.'}), 500

        url = "https://simple-instagram-api.p.rapidapi.com/account-info"
        querystring = {"username": username}

        headers = {
            "X-RapidAPI-Key": rapidapi_key,
            "X-RapidAPI-Host": "simple-instagram-api.p.rapidapi.com"
        }

        print("Sending request to Instagram API...")
        response = requests.get(url, headers=headers, params=querystring)
        print(f"API response status code: {response.status_code}")
        print(f"API response text: {response.text}")

        if response.status_code != 200:
            print("API returned non-200 status code")
            return jsonify({'success': False, 'error': f"API Error: {response.status_code} - {response.text}"}), 500

        response_data = response.json()
        print("API response JSON loaded")
        print(f"API response keys: {list(response_data.keys())}")

        # --- FIXED INDENTATION STARTS HERE ---
        try:
            # Handle different API response structures
            # Try to get profile picture URL - check different possible field names
            p_url = None
            if 'profile_pic_url_hd' in response_data:
                p_url = response_data['profile_pic_url_hd']
            elif 'profile_pic_url' in response_data:
                p_url = response_data['profile_pic_url']
            elif 'profile_picture' in response_data:
                p_url = response_data['profile_picture']

            if p_url:
                urllib.request.urlretrieve(p_url, 'static/images/pp.jpg')
                print("Profile picture downloaded")
            else:
                print("No profile picture URL found in response")

            # Extract features with fallbacks for missing fields
            new_data = {
                'profile pic': 0 if "44884218_345707102882519_2446069589734326272_n.jpg" in str(response_data.get('profile_pic_url', '')) else 1,
                'nums/length username': sum([1 for x in username if x.isdigit()]) / len(username),
                'fullname words': len(list(response_data.get('full_name', '').split())),
                'nums/length fullname': sum([1 for x in response_data.get('full_name', '') if x.isdigit()]) / len(response_data.get('full_name', '')) if response_data.get('full_name') else 0,
                'name==username': 1 if username == response_data.get('full_name', '') else 0,
                'description length': len(response_data.get('biography', '')),
                'external URL': 1 if response_data.get('external_url') and response_data.get('external_url') != "null" else 0,
                '#posts': response_data.get('edge_owner_to_timeline_media', {}).get('count', 0) if isinstance(response_data.get('edge_owner_to_timeline_media'), dict) else 0,
                '#followers': response_data.get('edge_followed_by', {}).get('count', 0) if isinstance(response_data.get('edge_followed_by'), dict) else 0,
                '#follows': response_data.get('edge_follow', {}).get('count', 0) if isinstance(response_data.get('edge_follow'), dict) else 0,
                'private': 1 if response_data.get('is_private', False) else 0
            }

            # Alternative field names that might exist in the new API
            if new_data['#posts'] == 0:
                new_data['#posts'] = response_data.get('posts_count', 0) or response_data.get('media_count', 0) or 0
            if new_data['#followers'] == 0:
                new_data['#followers'] = response_data.get('followers_count', 0) or response_data.get('follower_count', 0) or 0
            if new_data['#follows'] == 0:
                new_data['#follows'] = response_data.get('following_count', 0) or response_data.get('follows_count', 0) or 0

            print("Features extracted successfully")
            print(f"Extracted features: {new_data}")

        except Exception as feature_error:
            print(f"Feature extraction error: {feature_error}")
            traceback.print_exc()
            return f"Error extracting features: {str(feature_error)}", 500
        # --- FIXED INDENTATION ENDS HERE ---

        if model is None:
            print("Model is not loaded")
            return "Model not loaded", 500

        print("Creating DataFrame for prediction...")
        new_df = pd.DataFrame([new_data])
        print(f"DataFrame for prediction:\n{new_df}")

        try:
            prediction = model.predict(new_df)
            print(f"Model prediction: {prediction}")
        except Exception as model_error:
            print(f"Model prediction error: {model_error}")
            traceback.print_exc()
            return f"Error during prediction: {str(model_error)}", 500

        final_result = "Fake" if prediction[0] == 1 else "Real"
        print(f"Final result: {final_result}")

        try:
            with open('result_data.json', 'w') as file:
                json.dump({'result': final_result, 'response': response_data}, file)
            print("Result data saved to result_data.json")
        except Exception as file_error:
            print(f"Error saving result data: {file_error}")
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(file_error)}), 500

        # Always return JSON for AJAX
        return jsonify({'success': True, 'redirect': url_for('result')})
    except Exception as e:
        print(f"General error in /predict route: {e}")
        traceback.print_exc()
        return f"Error: {str(e)}", 500

@app.route('/result')
@login_required
def result():
    if not db:
        print("Database not initialized in /result.")
        return "Database not initialized. Cannot view result.", 500
    try:
        with open('result_data.json', 'r') as file:
            data = json.load(file)
            final_result = data['result']
            response_data = data['response']
        print(f"Result page loaded: {final_result}, {response_data}")
        return render_template('result.html', result=final_result, response=response_data)
    except Exception as e:
        print(f"Error in result route: {e}")
        traceback.print_exc()
        return render_template('result.html', error=f"An unexpected error occurred: {str(e)}")

@app.route('/report')
@login_required
def report():
    if not db:
        return "Database not initialized. Cannot report.", 500
    try:
        with open('result_data.json', 'r') as file:
            data = json.load(file)
            final_result = data['result']
        print(new_data)
        new_data['fake'] = 1 if final_result =="Real" else 0
        field_names = ['profile pic', 'nums/length username', 'fullname words', 'nums/length fullname', 'name==username',
                       'description length', 'external URL', 'private', '#posts', '#followers', '#follows', 'fake'
                       ]
        with open('dataset.csv', 'a') as f_object:
            dict_writer_object = DictWriter(f_object, fieldnames=field_names)
            dict_writer_object.writerow(new_data)
            f_object.close()
        train()
        global model
        model = joblib.load('insta_model.joblib')
        return redirect(url_for('index'))
    except Exception as e:
        print(f"Error in report route: {e}")
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    # Initial training is kept here for development, but should be run separately in production.
    train()
    app.run(debug=True, host='0.0.0.0', port=5000)
