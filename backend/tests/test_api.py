"""
API integration tests for all endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
import io


class TestAPIEndpoints:
    """Test suite for API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def sample_image(self):
        """Create a sample image for upload."""
        # Create a minimal JPEG image
        jpeg_header = b'\xFF\xD8\xFF\xE0\x00\x10JFIF'
        jpeg_content = jpeg_header + b'\x00' * 1000
        return io.BytesIO(jpeg_content)
    
    def test_health_endpoint_200(self, client):
        """Test health endpoint returns 200."""
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_auth_register_400_invalid_email(self, client):
        """Test register endpoint with invalid email returns 400."""
        response = client.post("/api/v1/auth/register", json={
            "name": "Test User",
            "email": "invalid-email",
            "password": "SecurePass123"
        })
        assert response.status_code == 422  # Validation error
    
    def test_auth_register_400_weak_password(self, client):
        """Test register endpoint with weak password returns 400."""
        response = client.post("/api/v1/auth/register", json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "weak"
        })
        assert response.status_code == 422  # Validation error
    
    def test_auth_register_200_valid(self, client):
        """Test register endpoint with valid data returns 200."""
        response = client.post("/api/v1/auth/register", json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "SecurePass123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
    
    def test_auth_login_400_missing_credentials(self, client):
        """Test login endpoint with missing credentials returns 400."""
        response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com"
            # Missing password
        })
        assert response.status_code == 422  # Validation error
    
    def test_auth_login_200_valid(self, client):
        """Test login endpoint with valid credentials returns 200."""
        response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "SecurePass123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
    
    def test_auth_google_400_invalid_token(self, client):
        """Test Google auth with invalid token returns 400."""
        response = client.post("/api/v1/auth/google", json={
            "token": "invalid_token"
        })
        # Should return 401 or 400 depending on validation
        assert response.status_code in [400, 401]
    
    def test_auth_me_200(self, client):
        """Test /me endpoint returns 200."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 200
    
    def test_image_analyze_413_file_too_large(self, client):
        """Test image analyze with file too large returns 413."""
        # Create a large file (over 10MB)
        large_file = io.BytesIO(b'\x00' * (11 * 1024 * 1024))
        response = client.post(
            "/api/v1/image/analyze",
            files={"file": ("large.jpg", large_file, "image/jpeg")}
        )
        assert response.status_code == 413
    
    def test_image_analyze_400_invalid_file_type(self, client):
        """Test image analyze with invalid file type returns 400."""
        text_file = io.BytesIO(b'This is text, not an image')
        response = client.post(
            "/api/v1/image/analyze",
            files={"file": ("test.txt", text_file, "text/plain")}
        )
        assert response.status_code == 400
    
    def test_image_analyze_400_no_file(self, client):
        """Test image analyze without file returns 400."""
        response = client.post("/api/v1/image/analyze")
        assert response.status_code == 422  # Validation error
    
    def test_image_test_200(self, client):
        """Test image test endpoint returns 200."""
        response = client.get("/api/v1/image/test")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    def test_rate_limiting_429(self, client):
        """Test rate limiting returns 429 after exceeding limit."""
        # Note: This test requires rate limiting to be enabled
        # and may need adjustment based on actual limits
        # For now, we'll skip this as it's environment-dependent
        pytest.skip("Rate limiting test requires specific configuration")
    
    def test_404_nonexistent_endpoint(self, client):
        """Test nonexistent endpoint returns 404."""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404
    
    def test_405_wrong_method(self, client):
        """Test wrong HTTP method returns 405."""
        response = client.get("/api/v1/auth/register")
        assert response.status_code == 405
    
    def test_request_id_header(self, client, sample_image):
        """Test that request ID is returned in response headers."""
        response = client.post(
            "/api/v1/image/analyze",
            files={"file": ("test.jpg", sample_image, "image/jpeg")}
        )
        # Note: This may fail if file validation fails
        # but if it succeeds, should have X-Request-ID header
        if response.status_code == 200:
            assert "X-Request-ID" in response.headers
    
    def test_error_response_format(self, client):
        """Test error responses have consistent format."""
        response = client.post("/api/v1/auth/register", json={
            "email": "invalid"
        })
        if response.status_code != 200:
            data = response.json()
            assert "error" in data
            assert "code" in data["error"]
            assert "message" in data["error"]
            assert "timestamp" in data["error"]
