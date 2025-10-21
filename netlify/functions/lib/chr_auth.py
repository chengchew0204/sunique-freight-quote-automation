"""
C.H. Robinson Authentication
Copied from development/chr_auth.py
"""

import requests
from datetime import datetime, timedelta


class CHRobinsonAuth:
    """Handles OAuth 2.0 authentication for C.H. Robinson API"""
    
    def __init__(self, client_id, client_secret, environment='sandbox'):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = ('https://sandbox-api.navisphere.com' if environment == 'sandbox' 
                        else 'https://api.navisphere.com')
        self.token = None
        self.token_expiry = None
    
    def get_token(self):
        """Get valid access token, refreshing if necessary"""
        if self.token and self.token_expiry and datetime.now() < self.token_expiry:
            return self.token
        
        # Request new token
        url = f'{self.base_url}/v1/oauth/token'
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "audience": "https://inavisphere.chrobinson.com",
            "grant_type": "client_credentials"
        }
        
        response = requests.post(url, json=payload, 
                                headers={'Content-Type': 'application/json'})
        
        if response.status_code == 200:
            data = response.json()
            self.token = data['access_token']
            expires_in = data.get('expires_in', 86400)
            # Refresh 1 hour early for safety
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in - 3600)
            return self.token
        else:
            raise Exception(f"Auth failed: {response.status_code} - {response.text}")
    
    def get_headers(self):
        """Get headers with valid bearer token"""
        return {
            'Authorization': f'Bearer {self.get_token()}',
            'Content-Type': 'application/json'
        }

