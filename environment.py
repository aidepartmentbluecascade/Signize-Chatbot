import os
from dotenv import load_dotenv

def load_environment():
    load_dotenv()
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        raise ValueError("OpenAI API key is missing in the environment variables.")
    
    # MongoDB configuration (optional - will use default if not set)
    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    
    # Set MongoDB URI in environment for other modules to use
    os.environ["MONGODB_URI"] = mongodb_uri
    
    return openai_key

def get_mongodb_uri():
    """Get MongoDB URI from environment variables"""
    load_dotenv()
    return os.getenv("MONGODB_URI", "mongodb://localhost:27017/")

def get_flask_config():
    """Get Flask configuration for production deployment"""
    load_dotenv()
    return {
        'FLASK_ENV': os.getenv('FLASK_ENV', 'production'),
        'FLASK_DEBUG': os.getenv('FLASK_DEBUG', 'false').lower() == 'true',
        'FLASK_SECRET_KEY': os.getenv('FLASK_SECRET_KEY', os.urandom(24).hex())
    }

def get_google_credentials():
    """Get Google credentials from environment variables or file"""
    load_dotenv()
    
    # Check if credentials are provided via environment variables
    if os.getenv("GOOGLE_CREDENTIALS_JSON"):
        try:
            import json
            creds_json = json.loads(os.getenv("GOOGLE_CREDENTIALS_JSON"))
            from google.oauth2.service_account import Credentials
            return Credentials.from_service_account_info(creds_json)
        except Exception as e:
            print(f"⚠️  Error parsing Google credentials from environment: {e}")
            return None
    
    # Fallback to credentials.json file
    if os.path.exists('credentials.json'):
        try:
            from google.oauth2.service_account import Credentials
            return Credentials.from_service_account_file('credentials.json')
        except Exception as e:
            print(f"⚠️  Error loading Google credentials from file: {e}")
            return None
    
    return None
