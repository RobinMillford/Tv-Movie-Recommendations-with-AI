# File: app.py
from flask import Flask
from flask_login import LoginManager
from dotenv import load_dotenv
import os
from datetime import timedelta
import urllib.parse

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")

# Configure database with SSL support for Render
database_url = os.getenv("DATABASE_URL")
if database_url:
    # Handle PostgreSQL SSL requirement on Render
    if database_url.startswith("postgresql://"):
        # Parse the URL and add SSL parameters if not already present
        parsed = urllib.parse.urlparse(database_url)
        if not parsed.query:
            # Add SSL mode requirement for Render PostgreSQL
            database_url += "?sslmode=require"
        elif "sslmode" not in parsed.query:
            database_url += "&sslmode=require"
    
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Debug: Print the database URI to verify it's correct
print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'

# Configure remember me cookie duration (30 days)
login_manager.remember_cookie_duration = timedelta(days=30)

# Import and register blueprints
from routes.main import main
from routes.chat import chat
from routes.details import details
from routes.auth import auth

app.register_blueprint(auth)
app.register_blueprint(main)
app.register_blueprint(chat)
app.register_blueprint(details)

# Initialize database after blueprints to avoid circular imports
from models import db, User
db.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create tables only if they don't exist
with app.app_context():
    # Debug: Print the actual database engine being used
    print(f"Database engine: {db.engine}")
    db.create_all()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)