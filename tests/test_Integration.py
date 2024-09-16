import unittest
from application import app, db
from models.models import Election, Candidate, Vote, User
from flask_login import login_user

class ElectionIntegrationTestCase(unittest.TestCase):

    def setUp(self):
        """Set up the test client and database."""
        self.app = app.test_client()
        self.app.testing = True
        self.app_context = app.app_context()
        self.app_context.push()

        # Start a nested transaction to roll back after each test
        db.session.begin_nested()

        # Create a user for testing
        self.user = User(username="testuser")
        self.user.set_password("password")
        db.session.add(self.user)
        db.session.commit()

    def tearDown(self):
        """Rollback the session instead of dropping the tables."""
        db.session.rollback()
        db.session.remove()
        self.app_context.pop()

    def login(self):
        """Helper method to log in the test user."""
        return self.app.post('/login', data={
            'username': 'testuser',
            'password': 'password'
        }, follow_redirects=True)

    def test_restaurant_election_workflow(self):
        """Test the workflow of setting up an election, voting, and viewing results."""
        
        # Log in the user
        self.login()

        # Step 1: Set up a restaurant election
        response = self.app.post('/setup_restaurant_election', data={
            'city': 'New York',
            'state': 'NY',
            'number_of_restaurants': '3',
            'max_votes': '5',
            'election_name': 'Restaurant Election'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"started", response.data)

        # Step 2: Verify the election exists in the database
        election = Election.query.filter_by(election_name="Restaurant Election").first()
        self.assertIsNotNone(election)
        candidates = Candidate.query.filter_by(election_id=election.id).all()
        self.assertEqual(len(candidates), 3)

        # Step 3: Submit a vote for the first candidate
        response = self.app.post(f'/vote/{election.id}', data={'candidate': candidates[0].id}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Step 4: Verify that the user cannot vote again in the same election
        response = self.app.post(f'/vote/{election.id}', data={'candidate': candidates[1].id}, follow_redirects=True)
        self.assertIn(b"You have already voted", response.data)  # Assuming this message is shown

        # Step 5: Verify the vote was recorded in the database
        votes_for_first_candidate = Vote.query.filter_by(candidate_id=candidates[0].id).count()
        self.assertEqual(votes_for_first_candidate, 1)

        # Step 6: Verify the results page renders correctly
        response = self.app.get(f'/results/{election.id}')
        self.assertEqual(response.status_code, 200)

        # Verify that the response contains the expected vote percentages
        response_text = response.data.decode('utf-8')
        self.assertIn("100.0%", response_text)  # 1 vote out of 1 for first candidate
