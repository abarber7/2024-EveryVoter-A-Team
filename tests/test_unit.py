import unittest
import sys
import os
from unittest.mock import MagicMock, Mock, patch
from election_service import ElectionService
from flask import url_for

# Adds project root directory to sys.path for imports
sys.path.insert(0, os.path.abspath(".."))

# Imports the Flask app, database, and models
from application import create_app, db
from models import User, Election, Candidate, Vote, UserVote
from register_routes import RegisterRoutes

# Helper function for calculating total votes
def calculate_results(vote_data):
    # Calculates total votes from a list of dictionaries containing vote counts
    if not isinstance(vote_data, list):
        raise TypeError("vote_data must be a list of dictionaries with 'votes' as an integer.")
    total_votes = sum(item['votes'] for item in vote_data if isinstance(item.get('votes'), int))
    return total_votes  # Returns the total number of votes

# Helper function to format election results
def format_election_results(results):
    # Formats election results into a string with candidate names and vote counts
    return "\n".join(f"{candidate}: {votes} votes" for candidate, votes in results.items())

# Test class for utility functions like calculate_results and format_election_results
class TestUtils(unittest.TestCase):

    def setUp(self):
        # Sets up the Flask app with 'testing' configuration and initializes the database
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()  # Initializes the database tables

    def tearDown(self):
        # Cleans up database and app context after each test
        db.session.remove()
        db.drop_all()  # Drops all tables from the database
        self.app_context.pop()  # Pops the app context

    def test_calculate_results_sum(self):
        # Tests summing of votes to ensure proper calculation
        results = calculate_results([{'votes': 100}, {'votes': 200}, {'votes': 50}])
        self.assertEqual(results, 350)  # Asserts that the total vote count is 350

    def test_calculate_results_empty(self):
        # Ensures calculate_results returns 0 for an empty list
        results = calculate_results([])
        self.assertEqual(results, 0)  # Asserts that the total vote count is 0 for empty input

    def test_calculate_results_with_invalid_data_type(self):
        # Ensures TypeError is raised if input is not a list
        with self.assertRaises(TypeError):
            calculate_results("invalid_data")  # Triggers TypeError for non-list input

    def test_format_election_results(self):
        # Tests formatting of election results with candidate names and vote counts
        formatted_result = format_election_results({'Candidate A': 100, 'Candidate B': 200})
        self.assertEqual(formatted_result, "Candidate A: 100 votes\nCandidate B: 200 votes")
        # Verifies the formatted result is correct

    def test_format_election_results_empty(self):
        # Ensures format_election_results handles an empty dictionary correctly
        formatted_result = format_election_results({})
        self.assertEqual(formatted_result, "")  # Asserts that the result is an empty string for no input

# Test class for the data models (User, Election, Candidate, Vote, and UserVote)
class TestModels(unittest.TestCase):

    def setUp(self):
        # Sets up the Flask app and initializes the database schema for testing
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()  # Initializes all database tables

    def tearDown(self):
        # Cleans up database session and app context after each test
        db.session.remove()
        db.drop_all()  # Drops all tables to reset the database
        self.app_context.pop()  # Pops the app context

    def test_create_user(self):
        # Tests creation of User, password hashing, and retrieval
        user = User(username="testuser")
        user.set_password("testpass")
        db.session.add(user)
        db.session.commit()
        saved_user = User.query.filter_by(username="testuser").first()
        self.assertEqual(saved_user.username, "testuser")
        self.assertTrue(saved_user.check_password("testpass"))  # Verifies password hash

    def test_user_invalid_password(self):
        # Tests that an incorrect password returns False in check_password
        user = User(username="testuser")
        user.set_password("testpass")
        self.assertFalse(user.check_password("wrongpass"))  # Ensures password check fails for wrong password

    def test_user_str_method(self):
        # Checks string representation of User
        user = User(username="testuser")
        self.assertEqual(str(user), "User testuser")  # Verifies that __str__ method outputs correctly

    def test_create_election(self):
        # Tests creation and retrieval of an Election object
        election = Election(election_name="General Election", election_type="Presidential", max_votes=3)
        db.session.add(election)
        db.session.commit()
        saved_election = Election.query.filter_by(election_name="General Election").first()
        self.assertEqual(saved_election.election_name, "General Election")
        self.assertEqual(saved_election.election_type, "Presidential")  # Checks the election data

    def test_election_str_method(self):
        # Checks string representation of Election
        election = Election(election_name="General Election", election_type="Presidential", max_votes=3)
        self.assertEqual(str(election), "General Election (Presidential)")  # Verifies __str__ output for Election

    def test_create_candidate(self):
        # Tests creation of a Candidate within an Election
        election = Election(election_name="General Election", election_type="Presidential", max_votes=3)
        db.session.add(election)
        db.session.commit()
        candidate = Candidate(name="Candidate A", election_id=election.id)
        db.session.add(candidate)
        db.session.commit()
        saved_candidate = Candidate.query.filter_by(name="Candidate A").first()
        self.assertEqual(saved_candidate.name, "Candidate A")  # Ensures candidate data is saved correctly

    def test_create_vote(self):
        # Tests Vote creation linked to a Candidate and Election
        election = Election(election_name="General Election", election_type="Presidential", max_votes=3)
        db.session.add(election)
        db.session.commit()
        candidate = Candidate(name="Candidate A", election_id=election.id)
        db.session.add(candidate)
        db.session.commit()
        vote = Vote(candidate_id=candidate.id, election_id=election.id)
        db.session.add(vote)
        db.session.commit()
        saved_vote = Vote.query.filter_by(candidate_id=candidate.id).first()
        self.assertEqual(saved_vote.candidate_id, candidate.id)  # Verifies vote is linked correctly

    def test_create_user_vote(self):
        # Tests UserVote creation to track user participation in an Election
        user = User(username="testuser")
        user.set_password("testpass")
        db.session.add(user)
        db.session.commit()
        election = Election(election_name="General Election", election_type="Presidential", max_votes=3)
        db.session.add(election)
        db.session.commit()
        user_vote = UserVote(user_id=user.id, election_id=election.id)
        db.session.add(user_vote)
        db.session.commit()
        saved_user_vote = UserVote.query.filter_by(user_id=user.id).first()
        self.assertEqual(saved_user_vote.user_id, user.id)  # Confirms UserVote links user and election

class TestRegisterRoutes(unittest.TestCase):

    def setUp(self):
        # Sets up the Flask app with 'testing' configuration
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Configures the app for testing and initializes the database
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['SERVER_NAME'] = 'localhost'
        
        # Initializes database and test client
        db.create_all()
        self.client = self.app.test_client()  # Creates a test client for HTTP requests

    def tearDown(self):
        # Cleans up database and app context after each test
        db.session.remove()
        db.drop_all()
        self.app_context.pop()  # Pops the app context after the test

    @patch('flask_login.utils._get_user')
    def test_setup_custom_election(self, mock_current_user):
        # Mock a user with the admin role
        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_user.role = 'admin'
        mock_current_user.return_value = mock_user  # Sets mock user as admin

        # Set up test data for custom election
        with self.client as client:
            response = client.post('/setup_custom_election', data={
                'election_name': 'Custom Test Election',
                'election_type': 'Presidential',
                'max_votes_custom': '5',
                'candidate_names[]': 'Candidate A'  # Ensure at least one candidate is provided
            }, content_type='application/x-www-form-urlencoded', follow_redirects=True)

            # Verify response status
            self.assertEqual(response.status_code, 200)

            # Check for a substring that confirms successful creation
            self.assertIn(b"Custom election &#39;Custom Test Election&#39; started with ID", response.data)
            # Checks for success message in HTML response

    def test_home_route(self):
        # Tests that the home route is accessible
        with self.client as client:
            response = client.get('/')
            self.assertEqual(response.status_code, 200)  # Confirms home route status is OK

    def test_view_election_results(self):
        # Tests the election results viewing route
        with self.client as client:
            # Set up an election to view results for
            election = Election(election_name="Sample Election", election_type="General", max_votes=50)
            db.session.add(election)
            db.session.commit()

            # Test the results route
            response = client.get(f'/results/{election.id}')
            self.assertEqual(response.status_code, 200)  # Ensures route for viewing results works

class TestElectionService(unittest.TestCase):
    def setUp(self):
        # Set up the Flask app and database for testing
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.mock_model = MagicMock()
        self.election_service = ElectionService(model=self.mock_model, db=db)  # Initializes service with mock model

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()  # Cleans up database and context

    def test_start_election_creates_election_and_candidates(self):
        # Tests starting an election and creating associated candidates
        candidates = ["Alice", "Bob"]
        election_id = self.election_service.start_election(
            candidates, max_votes=100, election_type="General", election_name="Sample Election"
        )
        # Update from Election.query.get() to db.session.get() to avoid LegacyAPIWarning
        election = db.session.get(Election, election_id)
        self.assertIsNotNone(election)
        self.assertEqual(election.election_name, "Sample Election")
        self.assertEqual(len(election.candidates), 2)  # Verifies two candidates were added

    def test_ordinal_function(self):
        # Tests ordinal number formatting for integers
        self.assertEqual(self.election_service.ordinal(1), "1st")
        self.assertEqual(self.election_service.ordinal(2), "2nd")
        self.assertEqual(self.election_service.ordinal(3), "3rd")
        self.assertEqual(self.election_service.ordinal(11), "11th")
        self.assertEqual(self.election_service.ordinal(21), "21st")
        
        # Checks exception for non-integer input
        with self.assertRaises(ValueError):
            self.election_service.ordinal("invalid")  # Ensures ValueError for invalid input

    def test_generate_gpt4_text_introduction(self):
        # Tests generating introductions for candidates
        election = Election(election_name="Test Election", election_type="General", max_votes=100)
        db.session.add(election)
        db.session.commit()
        
        candidate1 = Candidate(name="Alice", election_id=election.id)
        candidate2 = Candidate(name="Bob", election_id=election.id)
        db.session.add_all([candidate1, candidate2])
        db.session.commit()

        # Set up mock responses for generated introductions
        self.mock_model.invoke.side_effect = [
            MagicMock(content="Introducing 1st, the vibrant Alice!"),
            MagicMock(content="Introducing 2nd, the charismatic Bob!")
        ]
        
        introductions = self.election_service.generate_gpt4_text_introduction(election)
        self.assertEqual(len(introductions), 2)
        self.assertEqual(introductions[0], "Introducing 1st, the vibrant Alice!")
        self.assertEqual(introductions[1], "Introducing 2nd, the charismatic Bob!")
        # Verifies correct introductions generated for each candidate

    def test_get_restaurant_candidates(self):
        # Tests restaurant name generation using GPT-4 model
        self.mock_model.invoke.return_value = MagicMock(content="Bistro One\nDine Delight\nEpicurean Spot")
        
        restaurant_candidates = self.election_service.get_restaurant_candidates(
            number_of_restaurants=3, city="Sample City", state="Sample State"
        )
        self.assertEqual(len(restaurant_candidates), 3)
        self.assertIn("Bistro One", restaurant_candidates)
        self.assertIn("Dine Delight", restaurant_candidates)
        self.assertIn("Epicurean Spot", restaurant_candidates)  # Verifies generated restaurant names

if __name__ == '__main__':
    unittest.main()
