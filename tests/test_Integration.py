import unittest
from flask import url_for
from application import create_app
from extensions import db

class TestHomepage(unittest.TestCase):
    def setUp(self):
        # Create the app with the 'testing' configuration
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Configure the app for testing
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        
        # Set SERVER_NAME to allow url_for to work in test environment
        self.app.config['SERVER_NAME'] = 'localhost'
        
        # Create the database tables
        db.create_all()
        
        # Create a test client
        self.client = self.app.test_client()

    def tearDown(self):
        # Remove the database and the app context
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_homepage_loads(self):
        with self.app.test_request_context():
            # Send a GET request to the homepage
            response = self.client.get('/')
            
            # Check if the request was successful
            self.assertEqual(response.status_code, 200)
            
            # Check if the response contains expected content
            self.assertIn(b'Choose Your Election', response.data)

if __name__ == '__main__':
    unittest.main()