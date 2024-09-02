import unittest
from main import app, DEFAULT_CANDIDATES, votes

class ApplicationStartupTestCase(unittest.TestCase):

    def setUp(self):
        """Set up the test client."""
        self.app = app.test_client()
        self.app.testing = True

    def test_home_page_loads(self):
        """Test that the home page loads successfully."""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Cast Your Vote', response.data)

if __name__ == "__main__":
    unittest.main()
