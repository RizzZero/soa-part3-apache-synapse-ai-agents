"""
Authentication and Authorization Manager

This module provides authentication and authorization capabilities for Apache Synapse MCP,
handling JWT, OAuth2, and API key authentication methods.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass
import jwt
import time
from datetime import datetime, timedelta
import aiohttp
from passlib.context import CryptContext

from ..core.config import SecurityConfig

logger = logging.getLogger(__name__)


@dataclass
class User:
    """User information."""
    id: str
    username: str
    email: str
    roles: list
    permissions: list
    active: bool = True


@dataclass
class AuthResult:
    """Authentication result."""
    success: bool
    user: Optional[User] = None
    token: Optional[str] = None
    error: Optional[str] = None
    expires_at: Optional[datetime] = None


class AuthManager:
    """
    Authentication and authorization manager that handles various
    authentication methods including JWT, OAuth2, and API keys.
    """
    
    def __init__(self, config: SecurityConfig):
        """Initialize the authentication manager."""
        self.config = config
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Token cache
        self._token_cache: Dict[str, Dict[str, Any]] = {}
        
        # User cache
        self._user_cache: Dict[str, User] = {}
    
    async def start(self):
        """Start the authentication manager."""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        logger.info("Authentication manager started")
    
    async def stop(self):
        """Stop the authentication manager."""
        if self.session:
            await self.session.close()
            self.session = None
        
        logger.info("Authentication manager stopped")
    
    async def authenticate_request(self, request: Any) -> bool:
        """
        Authenticate an MCP request.
        
        Args:
            request: The MCP request to authenticate
            
        Returns:
            True if authentication succeeds, False otherwise
        """
        if not self.config.enabled:
            return True
        
        try:
            # Extract authentication information from request
            auth_info = self._extract_auth_info(request)
            
            if not auth_info:
                logger.warning("No authentication information found in request")
                return False
            
            # Authenticate based on configured method
            if self.config.auth_type == "jwt":
                return await self._authenticate_jwt(auth_info)
            elif self.config.auth_type == "oauth2":
                return await self._authenticate_oauth2(auth_info)
            elif self.config.auth_type == "api_key":
                return await self._authenticate_api_key(auth_info)
            else:
                logger.error(f"Unsupported authentication type: {self.config.auth_type}")
                return False
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    def _extract_auth_info(self, request: Any) -> Optional[Dict[str, Any]]:
        """Extract authentication information from request."""
        # This is a simplified implementation
        # In a real implementation, you would extract auth info from the actual request object
        
        # For MCP requests, we might need to look at headers or other request properties
        # This is a placeholder implementation
        return {
            "type": "unknown",
            "credentials": None
        }
    
    async def _authenticate_jwt(self, auth_info: Dict[str, Any]) -> bool:
        """Authenticate using JWT token."""
        try:
            token = auth_info.get("credentials")
            if not token:
                return False
            
            # Decode and verify JWT
            payload = jwt.decode(
                token, 
                self.config.jwt_secret, 
                algorithms=["HS256"]
            )
            
            # Check if token is expired
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp) < datetime.now():
                logger.warning("JWT token expired")
                return False
            
            # Extract user information
            user_id = payload.get("sub")
            if not user_id:
                return False
            
            # Get or create user
            user = await self._get_user(user_id)
            if not user or not user.active:
                return False
            
            return True
            
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return False
        except Exception as e:
            logger.error(f"JWT authentication error: {e}")
            return False
    
    async def _authenticate_oauth2(self, auth_info: Dict[str, Any]) -> bool:
        """Authenticate using OAuth2 token."""
        try:
            token = auth_info.get("credentials")
            if not token:
                return False
            
            # Validate token with OAuth2 provider
            user_info = await self._validate_oauth2_token(token)
            if not user_info:
                return False
            
            # Get or create user
            user = await self._get_user(user_info["id"])
            if not user or not user.active:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"OAuth2 authentication error: {e}")
            return False
    
    async def _authenticate_api_key(self, auth_info: Dict[str, Any]) -> bool:
        """Authenticate using API key."""
        try:
            api_key = auth_info.get("credentials")
            if not api_key:
                return False
            
            # Validate API key
            user = await self._validate_api_key(api_key)
            if not user or not user.active:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"API key authentication error: {e}")
            return False
    
    async def _validate_oauth2_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate OAuth2 token with provider."""
        # This is a simplified implementation
        # In a real implementation, you would validate the token with the OAuth2 provider
        
        # For now, we'll just return a mock user info
        return {
            "id": "oauth2_user_123",
            "username": "oauth2_user",
            "email": "oauth2@example.com"
        }
    
    async def _validate_api_key(self, api_key: str) -> Optional[User]:
        """Validate API key and return associated user."""
        # This is a simplified implementation
        # In a real implementation, you would validate the API key against a database
        
        # For now, we'll just return a mock user
        return User(
            id="api_user_123",
            username="api_user",
            email="api@example.com",
            roles=["api_user"],
            permissions=["read", "write"]
        )
    
    async def _get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID from cache or database."""
        # Check cache first
        if user_id in self._user_cache:
            return self._user_cache[user_id]
        
        # In a real implementation, you would fetch from database
        # For now, we'll create a mock user
        user = User(
            id=user_id,
            username=f"user_{user_id}",
            email=f"user_{user_id}@example.com",
            roles=["user"],
            permissions=["read"]
        )
        
        # Cache the user
        self._user_cache[user_id] = user
        
        return user
    
    async def get_jwt_token(self) -> str:
        """Get a JWT token for authentication."""
        if not self.config.jwt_secret:
            raise ValueError("JWT secret not configured")
        
        # Create token payload
        payload = {
            "sub": "service_account",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        
        # Generate token
        token = jwt.encode(payload, self.config.jwt_secret, algorithm="HS256")
        
        return token
    
    async def get_oauth2_token(self) -> str:
        """Get an OAuth2 token for authentication."""
        if not self.config.oauth2_client_id or not self.config.oauth2_client_secret:
            raise ValueError("OAuth2 credentials not configured")
        
        # Check cache first
        cache_key = f"oauth2_{self.config.oauth2_client_id}"
        if cache_key in self._token_cache:
            cached = self._token_cache[cache_key]
            if cached["expires_at"] > datetime.now():
                return cached["token"]
        
        # Get new token from OAuth2 provider
        token = await self._get_oauth2_token_from_provider()
        
        # Cache the token
        self._token_cache[cache_key] = {
            "token": token,
            "expires_at": datetime.now() + timedelta(hours=1)
        }
        
        return token
    
    async def get_api_key(self) -> str:
        """Get an API key for authentication."""
        # In a real implementation, you would get this from configuration or database
        return "your-api-key-here"
    
    async def _get_oauth2_token_from_provider(self) -> str:
        """Get OAuth2 token from provider."""
        # This is a simplified implementation
        # In a real implementation, you would make a request to the OAuth2 provider
        
        # For now, we'll return a mock token
        return "mock_oauth2_token"
    
    def hash_password(self, password: str) -> str:
        """Hash a password."""
        return self.pwd_context.hash(password)
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify a password against its hash."""
        return self.pwd_context.verify(password, hashed)
    
    def has_permission(self, user: User, permission: str) -> bool:
        """Check if user has a specific permission."""
        return permission in user.permissions
    
    def has_role(self, user: User, role: str) -> bool:
        """Check if user has a specific role."""
        return role in user.roles
    
    def create_user(self, username: str, email: str, password: str, roles: list = None) -> User:
        """Create a new user."""
        if roles is None:
            roles = ["user"]
        
        user_id = f"user_{int(time.time())}"
        hashed_password = self.hash_password(password)
        
        user = User(
            id=user_id,
            username=username,
            email=email,
            roles=roles,
            permissions=["read"]  # Default permissions
        )
        
        # In a real implementation, you would save to database
        self._user_cache[user_id] = user
        
        return user
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        for user in self._user_cache.values():
            if user.username == username:
                return user
        return None
    
    def list_users(self) -> list:
        """List all users."""
        return list(self._user_cache.values())
    
    def update_user(self, user_id: str, **kwargs) -> Optional[User]:
        """Update user information."""
        if user_id not in self._user_cache:
            return None
        
        user = self._user_cache[user_id]
        
        # Update user attributes
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        return user
    
    def delete_user(self, user_id: str) -> bool:
        """Delete a user."""
        if user_id in self._user_cache:
            del self._user_cache[user_id]
            return True
        return False
    
    def clear_cache(self):
        """Clear all caches."""
        self._token_cache.clear()
        self._user_cache.clear()
        logger.info("Authentication caches cleared") 