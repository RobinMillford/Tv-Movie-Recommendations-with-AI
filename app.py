from flask import Flask
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# Import blueprints
from routes.main import main
from routes.chat import chat
from routes.details import details

# Register blueprints
app.register_blueprint(main)
app.register_blueprint(chat)
app.register_blueprint(details)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)