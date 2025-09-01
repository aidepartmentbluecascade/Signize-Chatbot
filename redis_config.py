#!/usr/bin/env python3
"""
Redis configuration for different environments
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class RedisConfig:
    """Redis configuration manager"""
    
    def __init__(self):
        self.host = os.getenv('REDIS_HOST', 'redis-14653.c10.us-east-1-4.ec2.redns.redis-cloud.com')
        self.port = int(os.getenv('REDIS_PORT', '14653'))
        self.db = int(os.getenv('REDIS_DB', '0'))
        self.password = os.getenv('REDIS_PASSWORD', None)
        self.ssl = False  # Redis Cloud doesn't require SSL for this connection
        self.timeout = int(os.getenv('REDIS_TIMEOUT', '5'))
        
        # Check if password is required but not provided
        if not self.password:
            print("⚠️  REDIS_PASSWORD not set in environment variables")
            print("   Please set REDIS_PASSWORD in your .env file or environment")
            print("   Example: REDIS_PASSWORD=your_redis_password")
        else:
            print(f"✅ Redis password found: {self.password[:8]}...")
        
    def get_connection_params(self):
        """Get Redis connection parameters"""
        params = {
            'host': self.host,
            'port': self.port,
            'db': self.db,
            'decode_responses': True,
            'socket_connect_timeout': self.timeout,
            'socket_timeout': self.timeout,
        }
        
        if self.password:
            params['password'] = self.password
            
        if self.ssl:
            params['ssl'] = True
            params['ssl_cert_reqs'] = None
            
        return params
    
    def get_url(self):
        """Get Redis URL for connection string"""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        else:
            return f"redis://{self.host}:{self.port}/{self.db}"
    
    def print_config(self):
        """Print current Redis configuration"""
        print(f"🔧 Redis Configuration:")
        print(f"  Host: {self.host}")
        print(f"  Port: {self.port}")
        print(f"  Database: {self.db}")
        print(f"  SSL: {self.ssl}")
        print(f"  Timeout: {self.timeout}s")
        print(f"  URL: {self.get_url()}")

# Global Redis config instance
redis_config = RedisConfig()

def test_redis_connection():
    """Test Redis connection"""
    import redis
    
    try:
        client = redis.Redis(**redis_config.get_connection_params())
        client.ping()
        print("✅ Redis connection successful!")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False

if __name__ == "__main__":
    redis_config.print_config()
    test_redis_connection()
