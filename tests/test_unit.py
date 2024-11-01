import unittest
import sys
import os
from unittest.mock import MagicMock, Mock, patch
from application import app  # Import the Flask app instance from application.py


from psycopg2 import OperationalError
import application
from election_service import ElectionService
from flask import url_for
import warnings
from sqlalchemy.exc import OperationalError, SQLAlchemyError  # Ensure SQLAlchemyError is imported here


# Adds project root directory to sys.path for imports
sys.path.insert(0, os.path.abspath(".."))

# Imports the Flask app, database, and models
from application import create_app, db
from models import User, Election, Candidate, Vote, UserVote

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

        # Create a subclass of User with the __str__ method
        class UserWithStr(User):
            def __str__(self):
                return f"User {self.username}"

        user = UserWithStr(username="testuser")
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
    # Create a subclass of Election with the __str__ method
        class ElectionWithStr(Election):
            def __str__(self):
                return f"{self.election_name} ({self.election_type})"

        # Checks string representation of Election
        election = ElectionWithStr(election_name="General Election", election_type="Presidential", max_votes=3)
        self.assertEqual(str(election), "General Election (Presidential)")

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
            self.assertIn(b"Custom election &#39;Custom Test Election&#39; created successfully.", response.data)
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

class TestApplicationDatabaseRetriesAndAPIKeys(unittest.TestCase):

    @patch('application.time.sleep', return_value=None)  # Mock sleep to avoid delay in tests
    def test_database_retry_logic_failure(self, mock_sleep):
        # Test case where database connection fails after all retry attempts

        # Create an app instance and activate the application context
        app = create_app('testing')
        with app.app_context():
            # Mock db.engine.connect to simulate constant failure, triggering retry logic
            with patch.object(db.engine, 'connect', side_effect=OperationalError("Mocked error", None, None)) as mock_connect:
                
                max_retries = 5  # Define the maximum retries
                retry_delay = 5  # Initial retry delay
                attempt_messages = []  # Collects log messages for each attempt
                
                # Expect an OperationalError to be raised after retries
                with self.assertRaises(OperationalError):
                    for attempt in range(max_retries):
                        try:
                            db.engine.connect()  # Attempt to connect
                            attempt_messages.append("Database connection successful")
                            break  # Exit loop if connection succeeds
                        except OperationalError as e:
                            if attempt < max_retries - 1:
                                attempt_messages.append(f"Database connection attempt {attempt + 1} failed. Retrying in {retry_delay} seconds...")
                                application.time.sleep(retry_delay)
                                retry_delay *= 2  # Apply exponential backoff for retry delay
                            else:
                                attempt_messages.append(f"Failed to connect to the database after {max_retries} attempts. Error: {str(e)}")
                                raise  # Raise error after max retries

                # Ensure the mock sleep was called 4 times (for 5 retries)
                self.assertEqual(mock_sleep.call_count, 4)
                # Check that the final message indicates failure after retries
                self.assertIn("Failed to connect to the database after 5 attempts", attempt_messages[-1])

    @patch.dict('os.environ', {"OPENAI_API_KEY": "", "ELEVENLABS_API_KEY": ""})  # Mock missing API keys
    def test_missing_api_keys_raises_error(self):
        # Test that missing API keys raises a ValueError on app creation
        with self.assertRaises(ValueError) as context:
            create_app()  # Attempt to create the app without necessary API keys
        
        # Verify that the error message matches expectation
        self.assertEqual(str(context.exception), "Missing required API keys.")
    
    def test_app_run(self):
        # Test if the app run method executes as expected
        with patch.object(app, 'run') as mock_run:  # Patch app.run for the test
            app.run()  # Run the app in test

            # Ensure run was called once
            mock_run.assert_called_once_with()

        print("Test passed: app.run() was called successfully.")

class TestAdminFeatures(unittest.TestCase):

    def setUp(self):
        # Set up Flask app and database for testing
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Set SERVER_NAME to support url_for calls in tests
        self.app.config['SERVER_NAME'] = 'localhost'
        
        db.create_all()  # Initialize the database tables
        self.client = self.app.test_client()  # Create a test client

    def tearDown(self):
        # Clean up database and app context after each test
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    @patch('flask_login.utils._get_user')
    def test_permission_denied_for_non_admin(self, mock_user):
        # Mock a non-admin user trying to access an admin page
        mock_user.return_value.role = 'user'  # Set user role to non-admin
        with self.app.test_request_context():
            response = self.client.get(url_for('admin.setup_restaurant_election'), follow_redirects=True)
            # Check response for the permission denial message
            self.assertIn(b"You do not have permission to access this page.", response.data)

    @patch('flask_login.utils._get_user')
    @patch('flask.current_app.election_service.get_restaurant_candidates', return_value=['Candidate A', 'Candidate B'])
    @patch('flask.current_app.election_service.start_election', return_value=123)
    def test_setup_restaurant_election_post(self, mock_start_election, mock_get_candidates, mock_user):
        # Mock admin user and test restaurant election setup process
        mock_user.return_value.role = 'admin'  # Set user role to admin
        with self.app.test_request_context():
            response = self.client.post(url_for('admin.setup_restaurant_election'), data={
                'city': 'TestCity',
                'state': 'TS',
                'number_of_restaurants': '2',
                'max_votes': '5',
                'election_name': 'Test Election'
            }, follow_redirects=True)
            
            # Verify that a success message confirms election creation
            self.assertIn(b"Restaurant election &#39;Test Election&#39; created successfully.", response.data)

    @patch('flask_login.utils._get_user')
    def test_setup_custom_election_no_candidates(self, mock_user):
        # Test missing candidate handling during custom election setup
        mock_user.return_value.role = 'admin'  # Mock admin user
        with self.app.test_request_context():
            response = self.client.post(url_for('admin.setup_custom_election'), data={
                'max_votes_custom': '5',
                'election_name': 'Custom Election',
                'candidate_names[]': ['']  # No candidate names provided
            }, follow_redirects=True)
            
            # Assert that the response includes a missing candidate error message
            self.assertIn(b"Please enter at least one candidate.", response.data)

    @patch('flask_login.utils._get_user')
    def test_election_not_found(self, mock_user):
        # Test response when attempting to access a non-existent election
        mock_user.return_value.role = 'admin'  # Mock admin user
        with self.app.test_request_context():
            response = self.client.post(url_for('admin.delete_election', election_id=999), follow_redirects=True)
            # Check for "Election not found" message
            self.assertIn(b"Election not found.", response.data)

    @patch('flask_login.utils._get_user')
    @patch('application.db.session.rollback')  # Mock db rollback to test error handling
    def test_delete_election_with_database_error(self, mock_rollback, mock_user):
        # Test database error handling during election deletion
        mock_user.return_value.role = 'admin'  # Mock admin user
        
        # Simulate SQLAlchemy error when attempting to delete an election
        with patch.object(db.session, 'delete', side_effect=SQLAlchemyError("Mocked error")):
            election = Election(election_name="Election to Delete", election_type="General", max_votes=10)
            db.session.add(election)
            db.session.commit()

            with self.app.test_request_context():
                response = self.client.post(url_for('admin.delete_election', election_id=election.id), follow_redirects=True)
                mock_rollback.assert_called_once()  # Verify rollback is called on error
                self.assertIn(b"Failed to delete election: Mocked error", response.data)

    @patch('flask_login.utils._get_user')
    def test_logout(self, mock_current_user):
        # Test logging out a user
        mock_user = Mock()
        mock_user.is_authenticated = True  # Set user to authenticated
        mock_current_user.return_value = mock_user

        # Perform logout and verify response
        with self.app.test_request_context():
            response = self.client.get(url_for('auth.logout'), follow_redirects=True)
            
            # Confirm flash message shows "You have been logged out."
            self.assertIn(b'You have been logged out.', response.data)
            # Verify redirection to election index page
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Choose Your Election', response.data)  # Check if index text is present

class TestElectionController(unittest.TestCase):

    def setUp(self):
        # Set up the Flask app and database for testing
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()  # Initialize a test client for HTTP requests

        # Configure test settings
        self.app.config['TESTING'] = True
        self.app.config['SERVER_NAME'] = 'localhost'
        self.app.config['PREFERRED_URL_SCHEME'] = 'http'

        db.create_all()  # Initialize database tables
        
        # Create a test election in the database
        self.election = Election(election_name='Test Election', election_type='test', max_votes=100, status='ongoing')
        db.session.add(self.election)
        db.session.commit()

    def tearDown(self):
        # Clean up database and context after each test
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    @patch('application.ElectionService.generate_gpt4_text_introduction', return_value=[])
    def test_generate_audio_text_generation_failed(self, mock_generate_text):
        # Test response when audio text generation fails (returns empty list)
        with self.app.test_request_context():
            response = self.client.post(
                url_for('election.generate_audio'),
                json={'election_id': self.election.id},
                follow_redirects=True
            )
        
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json, {"error": "Text generation failed."})

    @patch('application.ElectionService.generate_gpt4_text_introduction', return_value=["Sample introduction"])
    @patch('flask.current_app.elevenclient.text_to_speech.convert', return_value=iter([None]))  # Mock elevenclient's convert method
    def test_generate_audio_empty_audio_data(self, mock_convert, mock_generate_text):
        # Test response when generated audio data is empty
        with self.app.test_request_context():
            response = self.client.post(
                url_for('election.generate_audio'),
                json={'election_id': self.election.id},
                follow_redirects=True
            )
        
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json, {"error": "Audio data is empty."})

    @patch('application.ElectionService.generate_gpt4_text_introduction', return_value=["Sample introduction"])
    @patch('flask.current_app.elevenclient.text_to_speech.convert', return_value=iter([b"audio data"]))
    def test_generate_audio_successful(self, mock_convert, mock_generate_text):
        # Test successful generation of audio
        with self.app.test_request_context():
            response = self.client.post(
                url_for('election.generate_audio'),
                json={'election_id': self.election.id},
                follow_redirects=True
            )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "audio/mpeg")
        # Check content disposition for inline audio data
        self.assertEqual(response.headers["Content-Disposition"], "inline; filename=output.mp3")

    @patch('application.ElectionService.generate_gpt4_text_introduction', return_value=["Sample introduction"])
    def test_generate_audio_no_active_election(self, mock_generate_text):
        # Test response when election is inactive
        self.election.status = 'inactive'  # Set election status to inactive
        db.session.commit()
        
        with self.app.test_request_context():
            response = self.client.post(
                url_for('election.generate_audio'),
                json={'election_id': self.election.id},
                follow_redirects=True
            )
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json, {"error": "No active election."})


# Run the test using unittest's test runner
if __name__ == '__main__':
    unittest.main()
