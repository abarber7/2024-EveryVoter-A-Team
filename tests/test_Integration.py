import unittest
from flask import url_for
from application import create_app
from extensions import db
import sys
import os
from unittest.mock import patch, Mock

# Add project root directory to sys.path for imports
sys.path.insert(0, os.path.abspath(".."))

# Import Flask app, database, and models
from application import create_app, db
from models import User, Election, Candidate, Vote, UserVote

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


class TestIntegration(unittest.TestCase):
    # Integration tests covering user authentication, election lifecycle, voting process, and results retrieval

    def setUp(self):
        # Set up the Flask app with 'testing' configuration and initialize the database
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        # Clean up database and app context after each test
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    @patch('flask_login.utils._get_user')
    def test_admin_access_control(self, mock_current_user):
        # Test that only an authenticated admin can access admin routes
        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_user.role = 'admin'
        mock_current_user.return_value = mock_user

        response = self.client.get('/setup_custom_election')
        self.assertEqual(response.status_code, 200)

    def test_login_logout(self):
        # Test user login and logout functionality
        with self.client as client:
            response = client.post('/login', data={'username': 'testuser', 'password': 'testpass'})
            self.assertEqual(response.status_code, 302)

            response = client.get('/logout')
            self.assertEqual(response.status_code, 302)

    @patch('flask_login.utils._get_user')
    def test_election_creation(self, mock_current_user):
        # Test the lifecycle of creating an election as an admin
        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_user.role = 'admin'
        mock_current_user.return_value = mock_user

        response = self.client.post('/setup_custom_election', data={
            'election_name': 'Test Election',
            'election_type': 'General',
            'max_votes_custom': '5',
            'candidate_names[]': ['Candidate A', 'Candidate B']
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Election', response.data)

    @patch('flask_login.utils._get_user')
    def test_vote_submission(self, mock_current_user):
        # Mock a user with an authenticated session and a specific ID
        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_user.id = 1  # Ensure this ID matches the test user
        mock_current_user.return_value = mock_user

        # Create a user and election entry in the database
        user = User(username="testuser")
        user.set_password("testpass")
        user.id = 1  # Set the user ID to match mock_user.id
        db.session.add(user)

        # Create an election and set it up in the database
        election = Election(election_name="Sample Election", election_type="General", max_votes=50)
        db.session.add(election)
        db.session.commit()

        # Add a candidate to the created election
        candidate = Candidate(name="Candidate A", election_id=election.id)
        db.session.add(candidate)
        db.session.commit()

        # Perform a vote submission as a POST request
        response = self.client.post(f'/vote/{election.id}', data={
            'candidate': candidate.id  # Ensure field matches form expectations
        }, content_type='application/x-www-form-urlencoded', follow_redirects=True)

        # Verify the response and confirm submission success message is displayed
        self.assertEqual(response.status_code, 200)  # Ensure vote submission succeeded
        self.assertIn(b'Your vote has been recorded.', response.data)  # Check for success message


    @patch('flask_login.utils._get_user')
    def test_duplicate_vote(self, mock_current_user):
        # Mock an authenticated user
        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_user.id = 1
        mock_current_user.return_value = mock_user

        # Set up election and candidate
        election = Election(election_name="Test Election", election_type="General", max_votes=10)
        db.session.add(election)
        db.session.commit()
        candidate = Candidate(name="Candidate A", election_id=election.id)
        db.session.add(candidate)
        db.session.commit()

        # Submit the first vote
        db.session.add(UserVote(user_id=mock_user.id, election_id=election.id))
        db.session.commit()

        # Attempt a duplicate vote
        response = self.client.post(f'/vote/{election.id}', data={'candidate': candidate.id}, follow_redirects=True)
        
        # Check for the redirect and message
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'You have already voted in this election.', response.data)


    def test_election_results_retrieval(self):
        # Test retrieval of election results
        election = Election(election_name="Sample Election", election_type="General", max_votes=50)
        db.session.add(election)
        db.session.commit()

        # Add candidates and votes
        candidate1 = Candidate(name="Candidate A", election_id=election.id)
        candidate2 = Candidate(name="Candidate B", election_id=election.id)
        db.session.add_all([candidate1, candidate2])
        db.session.commit()

        # Simulate votes to set up a sample result
        db.session.add(Vote(candidate_id=candidate1.id, election_id=election.id))
        db.session.add(Vote(candidate_id=candidate2.id, election_id=election.id))
        db.session.commit()

        # Access results page
        response = self.client.get(f'/results/{election.id}')

        # Check for expected title in the response
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Election Results - Sample Election", response.data)


    def test_create_user_account(self):
        # Test creation of a new user account
        response = self.client.post('/register', data={
            'username': 'newuser',
            'password': 'newpass'
        })
        self.assertEqual(response.status_code, 302)

        user = User.query.filter_by(username='newuser').first()
        self.assertIsNotNone(user)

    @patch('flask_login.utils._get_user')
    def test_admin_can_delete_election(self, mock_current_user):
        # Test that an admin user can delete an election
        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_user.role = 'admin'
        mock_current_user.return_value = mock_user

        election = Election(election_name="Election to Delete", election_type="General", max_votes=10)
        db.session.add(election)
        db.session.commit()

        response = self.client.post(f'/delete_election/{election.id}', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        deleted_election = Election.query.get(election.id)
        self.assertIsNone(deleted_election)


    def test_view_all_elections(self):
        # Seeding: Manually add elections and ensure 'status' is set to 'ongoing'
        election1 = Election(election_name="Election 1", election_type="Local", max_votes=5, status="ongoing")
        election2 = Election(election_name="Election 2", election_type="National", max_votes=10, status="ongoing")
        db.session.add_all([election1, election2])
        db.session.commit()

        try:
            # Test: Send GET request to / to see if elections are displayed
            response = self.client.get("/")
            #print(response.data.decode())  # Debugging to confirm the response content

            # Assertions: Verify successful response and presence of elections
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Election 1', response.data)
            self.assertIn(b'Election 2', response.data)
        finally:
            # Cleanup to reset test database
            db.session.delete(election1)
            db.session.delete(election2)
            db.session.commit()
            

if __name__ == '__main__':
    unittest.main()