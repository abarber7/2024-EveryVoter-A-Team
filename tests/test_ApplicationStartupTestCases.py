import unittest
from sqlalchemy import text
from application import app, db  # Ensure that the database and app are imported

class ApplicationStartupTestCase(unittest.TestCase):

    def setUp(self):
        """Set up the test client and push application context."""
        self.app = app.test_client()
        self.app.testing = True
        self.app_context = app.app_context()
        self.app_context.push()  # Push the application context

    def tearDown(self):
        """Pop the application context after the test."""
        self.app_context.pop()

    def test_home_page_loads(self):
        """Test that the home page loads successfully."""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Choose Your Election', response.data)  # Updated to match actual content

    def test_database_connection(self):
        """Test that the database connection can be established."""
        try:
            # Use text() to wrap the raw SQL string
            db.session.execute(text('SELECT 1'))
            db.session.commit()
        except Exception as e:
            self.fail(f"Database connection failed: {e}")

if __name__ == "__main__":
    unittest.main()
