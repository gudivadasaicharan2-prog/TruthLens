"""
Unit tests for health check endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


class TestHealthEndpoints:
    """Test suite for health check endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_health_endpoint(self, client):
        """Test basic health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data
    
    def test_health_ready_endpoint(self, client):
        """Test readiness check endpoint."""
        response = client.get("/health/ready")
        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data
        assert "checks" in data
        assert "model" in data["checks"]
        assert "database" in data["checks"]
        assert "upload_dir" in data["checks"]
    
    def test_health_live_endpoint(self, client):
        """Test liveness check endpoint."""
        response = client.get("/health/live")
        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data
        assert "memory" in data
    
    def test_health_detailed_endpoint(self, client):
        """Test detailed health check endpoint."""
        response = client.get("/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "checks" in data
        assert "configuration" in data
        assert "model" in data["checks"]
        assert "gpu" in data["checks"]
        assert "database" in data["checks"]
        assert "memory" in data["checks"]
        assert "cpu" in data["checks"]
        assert "disk" in data["checks"]
