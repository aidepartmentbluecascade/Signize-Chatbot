import os
import json
import requests
from datetime import datetime, timedelta
from environment import get_dropbox_config

class DropboxAuth:
    def __init__(self):
        self.config = get_dropbox_config()
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
        
        if self.config:
            self.refresh_token = self.config.get('refresh_token')
            self.access_token = self.config.get('access_token')
            self._load_or_refresh_token()
    
    def _load_or_refresh_token(self):
        """Load existing token or refresh if expired"""
        if self.refresh_token:
            # Try to refresh the token
            self._refresh_access_token()
        elif self.access_token:
            # Use existing access token (will expire in 4 hours)
            print("⚠️  Using access token only (no refresh token). Token will expire in 4 hours.")
            print("   Run 'python setup_dropbox_simple.py' to get a refresh token for automatic renewal.")
        else:
            print("⚠️  No tokens available. Please set up OAuth2 authentication.")
    
    def _refresh_access_token(self):
        """Refresh the access token using the refresh token"""
        try:
            url = "https://api.dropboxapi.com/oauth2/token"
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token,
                'client_id': self.config['app_key'],
                'client_secret': self.config['app_secret']
            }
            
            response = requests.post(url, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data['access_token']
            
            # Set expiration time (tokens typically last 4 hours)
            self.token_expires_at = datetime.now() + timedelta(hours=4)
            
            print("✅ Dropbox access token refreshed successfully")
            
            # Save the new access token to environment (optional)
            os.environ['DROPBOX_ACCESS_TOKEN'] = self.access_token
            
        except Exception as e:
            print(f"❌ Failed to refresh Dropbox access token: {e}")
            self.access_token = None
    
    def get_access_token(self):
        """Get a valid access token, refreshing if necessary"""
        if not self.config:
            return None
        
        # If we have a refresh token, use it to refresh when needed
        if self.refresh_token:
            # Check if token is expired or will expire soon (within 5 minutes)
            if (not self.access_token or 
                not self.token_expires_at or 
                datetime.now() + timedelta(minutes=5) >= self.token_expires_at):
                self._refresh_access_token()
        # If we only have an access token, use it directly
        elif self.access_token:
            # For access token only, we can't refresh, so just return it
            # It will expire in 4 hours and need manual renewal
            pass
        
        return self.access_token
    
    def is_authenticated(self):
        """Check if we have valid authentication"""
        return self.get_access_token() is not None

def create_dropbox_client():
    """Create and return a Dropbox client with proper authentication"""
    import dropbox
    
    auth = DropboxAuth()
    if not auth.is_authenticated():
        print("❌ Dropbox authentication failed")
        return None
    
    try:
        dbx = dropbox.Dropbox(auth.get_access_token())
        # Test the connection
        account = dbx.users_get_current_account()
        print(f"✅ Connected to Dropbox as: {account.name.display_name}")
        return dbx
    except Exception as e:
        print(f"❌ Dropbox connection failed: {e}")
        return None
