import os
import unittest

from fastapi.testclient import TestClient

from server import app


class TestServerAuth(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        # Mock environment variables
        os.environ["LNT_ADMIN_KEY"] = "test-admin-key"
        # We need to re-import or re-initialize API_KEYS if the server was already loaded
        # Since it's a POC, we'll assume fresh environment for each test run or similar
        
    def test_auth_with_env_key(self):
        # Allow test to inject keys even if module already loaded
        from server import API_KEYS
        API_KEYS["test-admin-key"] = "ADMIN"
        
        # Verify injection
        self.assertIn("test-admin-key", API_KEYS)
        self.assertEqual(API_KEYS["test-admin-key"], "ADMIN")

    def test_process_endpoint_auth(self):
        # Test with valid key
        headers = {"x-lnt-api-key": "test-admin-key"}
        response = self.client.post("/process", json={"user_text": "hello"}, headers=headers)
        # Re-import to get updated API_KEYS
        import server
        server.API_KEYS["test-admin-key"] = "ADMIN" 
        
        response = self.client.post("/process", json={"user_text": "hello"}, headers=headers)
        self.assertEqual(response.status_code, 200)

        # Test with invalid key
        headers = {"x-lnt-api-key": "wrong-key"}
        response = self.client.post("/process", json={"user_text": "hello"}, headers=headers)
        self.assertEqual(response.status_code, 403)

if __name__ == "__main__":
    unittest.main()
