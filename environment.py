import os
from dotenv import load_dotenv

def load_environment():
    load_dotenv()
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        raise ValueError("OpenAI API key is missing in the environment variables.")

    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        print("⚠️  MONGODB_URI not found in environment variables")
        print("   Please set MONGODB_URI=your_atlas_connection_string")
        raise ValueError("MONGODB_URI environment variable is required")
 
    os.environ["MONGODB_URI"] = mongodb_uri
    print(f"✅ MongoDB URI loaded: {mongodb_uri[:50]}...")
    
    return openai_key

def get_mongodb_uri():
    """Get MongoDB URI from environment variables"""
    load_dotenv()
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        raise ValueError("MONGODB_URI environment variable is required")
    return mongodb_uri

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

    if os.getenv("GOOGLE_CREDENTIALS_JSON"):
        try:
            import json
            creds_json = json.loads(os.getenv("GOOGLE_CREDENTIALS_JSON"))
            from google.oauth2.service_account import Credentials
            return Credentials.from_service_account_info(creds_json)
        except Exception as e:
            print(f"⚠️  Error parsing Google credentials from environment: {e}")
            return None

    if os.path.exists('credentials.json'):
        try:
            from google.oauth2.service_account import Credentials
            return Credentials.from_service_account_file('credentials.json')
        except Exception as e:
            print(f"⚠️  Error loading Google credentials from file: {e}")
            return None
    
    return None

def get_dropbox_config():
    """Get Dropbox OAuth2 configuration from environment variables"""
    load_dotenv()
    
    config = {
        'app_key': os.getenv('DROPBOX_APP_KEY'),
        'app_secret': os.getenv('DROPBOX_APP_SECRET'),
        'refresh_token': os.getenv('DROPBOX_REFRESH_TOKEN'),
        'access_token': os.getenv('DROPBOX_ACCESS_TOKEN')
    }
    
    # Check if we have the minimum required credentials
    if not config['app_key'] or not config['app_secret']:
        print("⚠️  Dropbox OAuth2 credentials not found in environment variables")
        print("   Please set DROPBOX_APP_KEY and DROPBOX_APP_SECRET")
        return None
    
    return config

def get_hubspot_config():
    """Get HubSpot configuration from environment variables"""
    load_dotenv()
    
    hubspot_token = os.getenv('HUBSPOT_TOKEN')
    if not hubspot_token:
        print("⚠️  HUBSPOT_TOKEN not found in environment variables")
        print("   Please set HUBSPOT_TOKEN=your_hubspot_api_token")
        return None
    
    print(f"✅ HubSpot token loaded: {hubspot_token[:20]}...")
    return {
        'token': hubspot_token
    }
