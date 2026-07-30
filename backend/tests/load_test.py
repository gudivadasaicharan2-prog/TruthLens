"""
Load testing script using Locust for concurrent user simulation.
"""

from locust import HttpUser, task, between
import io
import random


class TruthLensUser(HttpUser):
    """
    Simulates a typical TruthLens user.
    """
    wait_time = between(1, 3)
    
    def on_start(self):
        """Called when a user starts."""
        # Login
        self.client.post("/api/v1/auth/login", json={
            "email": f"user{random.randint(1000, 9999)}@example.com",
            "password": "SecurePass123"
        })
    
    @task(3)
    def health_check(self):
        """Check health endpoint (lightweight)."""
        self.client.get("/health")
    
    @task(2)
    def check_ready(self):
        """Check readiness endpoint."""
        self.client.get("/health/ready")
    
    @task(1)
    def analyze_image(self):
        """
        Simulate image analysis.
        Note: This is a lightweight simulation without actual file upload.
        """
        # Create a minimal JPEG header
        jpeg_header = b'\xFF\xD8\xFF\xE0\x00\x10JFIF'
        jpeg_content = jpeg_header + b'\x00' * 1000
        
        files = {
            "file": ("test.jpg", io.BytesIO(jpeg_content), "image/jpeg")
        }
        
        # This may fail validation but tests the endpoint
        self.client.post("/api/v1/image/analyze", files=files)


class AdminUser(HttpUser):
    """
    Simulates an admin user checking detailed health.
    """
    wait_time = between(5, 10)
    
    @task
    def detailed_health_check(self):
        """Check detailed health endpoint."""
        self.client.get("/health/detailed")
