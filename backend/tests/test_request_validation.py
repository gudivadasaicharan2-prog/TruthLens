"""
Unit tests for request validation (auth models).
"""

import pytest
from pydantic import ValidationError
from app.api.v1.auth import RegisterRequest, LoginRequest, GoogleAuthRequest


class TestRequestValidation:
    """Test suite for request validation models."""
    
    def test_register_request_valid(self):
        """Test valid registration request."""
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "password": "SecurePass123",
            "role": "general"
        }
        request = RegisterRequest(**data)
        assert request.name == "John Doe"
        assert request.email == "john@example.com"
        assert request.role == "general"
    
    def test_register_request_name_too_short(self):
        """Test registration with name too short."""
        data = {
            "name": "J",
            "email": "john@example.com",
            "password": "SecurePass123"
        }
        with pytest.raises(ValidationError, match="at least 2 characters"):
            RegisterRequest(**data)
    
    def test_register_request_name_invalid_characters(self):
        """Test registration with invalid name characters."""
        data = {
            "name": "John<script>",
            "email": "john@example.com",
            "password": "SecurePass123"
        }
        with pytest.raises(ValidationError, match="invalid characters"):
            RegisterRequest(**data)
    
    def test_register_request_email_invalid(self):
        """Test registration with invalid email."""
        data = {
            "name": "John Doe",
            "email": "invalid-email",
            "password": "SecurePass123"
        }
        with pytest.raises(ValidationError, match="Invalid email format"):
            RegisterRequest(**data)
    
    def test_register_request_email_normalization(self):
        """Test email is normalized to lowercase."""
        data = {
            "name": "John Doe",
            "email": "JOHN@EXAMPLE.COM",
            "password": "SecurePass123"
        }
        request = RegisterRequest(**data)
        assert request.email == "john@example.com"
    
    def test_register_request_password_no_uppercase(self):
        """Test registration password without uppercase."""
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "password": "securepass123"
        }
        with pytest.raises(ValidationError, match="uppercase"):
            RegisterRequest(**data)
    
    def test_register_request_password_no_lowercase(self):
        """Test registration password without lowercase."""
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "password": "SECUREPASS123"
        }
        with pytest.raises(ValidationError, match="lowercase"):
            RegisterRequest(**data)
    
    def test_register_request_password_no_digit(self):
        """Test registration password without digit."""
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "password": "SecurePassword"
        }
        with pytest.raises(ValidationError, match="digit"):
            RegisterRequest(**data)
    
    def test_register_request_password_too_short(self):
        """Test registration password too short."""
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "password": "Short1"
        }
        with pytest.raises(ValidationError, match="at least 8 characters"):
            RegisterRequest(**data)
    
    def test_login_request_valid(self):
        """Test valid login request."""
        data = {
            "email": "john@example.com",
            "password": "SecurePass123"
        }
        request = LoginRequest(**data)
        assert request.email == "john@example.com"
    
    def test_login_request_email_invalid(self):
        """Test login with invalid email."""
        data = {
            "email": "invalid-email",
            "password": "SecurePass123"
        }
        with pytest.raises(ValidationError, match="Invalid email format"):
            LoginRequest(**data)
    
    def test_google_auth_request_valid(self):
        """Test valid Google auth request."""
        data = {
            "token": "eyJhbGciOiJSUzI1NiIsImtpZCI6Ij..."
        }
        request = GoogleAuthRequest(**data)
        assert request.token == data["token"]
    
    def test_google_auth_request_token_too_short(self):
        """Test Google auth with token too short."""
        data = {
            "token": "short"
        }
        with pytest.raises(ValidationError, match="at least 10 characters"):
            GoogleAuthRequest(**data)
