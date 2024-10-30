import unittest
import sys
import os

# Adds project root directory to sys.path
sys.path.insert(0, os.path.abspath(".."))

# Imports the Flask app, database, and models
from application import create_app, db
from models import User, Election, Candidate, Vote, UserVote

# Define helper functions for testing

def validate_voter_age(age):
    # Checks if age is 18 or older for voting eligibility
    return age >= 18

def calculate_results(vote_data):
    # Sums votes from a list of dictionaries with vote counts
    if not isinstance(vote_data, list):
        raise TypeError("vote_data must be a list of dictionaries with 'votes' as an integer.")
    total_votes = 0
    for item in vote_data:
        if not isinstance(item.get('votes'), int):
            raise TypeError("All 'votes' values must be integers.")
        total_votes += item['votes']
    return total_votes

def format_election_results(results):
    # Formats election results into a string with candidate names and vote counts
    return "\n".join(f"{candidate}: {votes} votes" for candidate, votes in results.items())

# Test class for utility functions
class TestUtils(unittest.TestCase):

    def setUp(self):
        # Sets up the Flask app with 'testing' configuration and initializes the database
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        # Cleans up database and app context after each test
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_validate_voter_age_valid(self):
        # Validates that age 25 returns True for voting eligibility
        self.assertTrue(validate_voter_age(25))

    def test_validate_voter_age_boundary(self):
        # Validates that exactly age 18 returns True for voting eligibility
        self.assertTrue(validate_voter_age(18))
    
    def test_validate_voter_age_invalid(self):
        # Validates that age 15 returns False for voting eligibility
        self.assertFalse(validate_voter_age(15))

    def test_calculate_results_sum(self):
        # Checks if calculate_results correctly sums vote counts
        results = calculate_results([{'votes': 100}, {'votes': 200}, {'votes': 50}])
        self.assertEqual(results, 350)

    def test_calculate_results_empty(self):
        # Ensures calculate_results returns 0 for an empty list
        results = calculate_results([])
        self.assertEqual(results, 0)

    def test_calculate_results_with_non_integer_votes(self):
        # Ensures TypeError is raised for non-integer vote values
        with self.assertRaises(TypeError):
            calculate_results([{'votes': 'one hundred'}])

    def test_calculate_results_with_invalid_data_type(self):
        # Ensures TypeError is raised if input is not a list
        with self.assertRaises(TypeError):
            calculate_results("invalid_data")

    def test_format_election_results(self):
        # Ensures format_election_results produces correct string formatting
        formatted_result = format_election_results({'Candidate A': 100, 'Candidate B': 200})
        self.assertEqual(formatted_result, "Candidate A: 100 votes\nCandidate B: 200 votes")

    def test_format_election_results_empty(self):
        # Ensures format_election_results handles an empty dictionary correctly
        formatted_result = format_election_results({})
        self.assertEqual(formatted_result, "")

# Test class for models
class TestModels(unittest.TestCase):

    def setUp(self):
        # Sets up the Flask app and initializes the database schema for testing
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        # Cleans up database session and app context after each test
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_create_user(self):
        # Tests User creation, password hashing, and retrieval
        user = User(username="testuser")
        user.set_password("testpass")
        db.session.add(user)
        db.session.commit()
        saved_user = User.query.filter_by(username="testuser").first()
        self.assertEqual(saved_user.username, "testuser")
        self.assertTrue(saved_user.check_password("testpass"))

    def test_user_invalid_password(self):
        # Tests that incorrect password returns False in check_password
        user = User(username="testuser")
        user.set_password("testpass")
        self.assertFalse(user.check_password("wrongpass"))

    def test_user_str_method(self):
        # Checks User string representation
        user = User(username="testuser")
        self.assertEqual(str(user), "User testuser")

    def test_create_election(self):
        # Tests Election creation with attributes and retrieval
        election = Election(election_name="General Election", election_type="Presidential", max_votes=3)
        db.session.add(election)
        db.session.commit()
        saved_election = Election.query.filter_by(election_name="General Election").first()
        self.assertEqual(saved_election.election_name, "General Election")
        self.assertEqual(saved_election.election_type, "Presidential")

    def test_election_str_method(self):
        # Checks Election string representation
        election = Election(election_name="General Election", election_type="Presidential", max_votes=3)
        self.assertEqual(str(election), "General Election (Presidential)")

    def test_create_candidate(self):
        # Tests Candidate creation within an Election and retrieval
        election = Election(election_name="General Election", election_type="Presidential", max_votes=3)
        db.session.add(election)
        db.session.commit()
        candidate = Candidate(name="Candidate A", election_id=election.id)
        db.session.add(candidate)
        db.session.commit()
        saved_candidate = Candidate.query.filter_by(name="Candidate A").first()
        self.assertEqual(saved_candidate.name, "Candidate A")

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
        self.assertEqual(saved_vote.candidate_id, candidate.id)

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
        self.assertEqual(saved_user_vote.user_id, user.id)

    def test_unique_username(self):
        # Tests that duplicate usernames raise an IntegrityError
        user1 = User(username="uniqueuser")
        user1.set_password("password1")
        db.session.add(user1)
        db.session.commit()
        
        user2 = User(username="uniqueuser")
        user2.set_password("password2")
        
        with self.assertRaises(Exception):  # IntegrityError expected
            db.session.add(user2)
            db.session.commit()

if __name__ == '__main__':
    unittest.main()
