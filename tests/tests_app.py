# tests_app.py

import unittest
import html  # Import html module to unescape HTML entities
from application import app, election_state

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

    def test_start_custom_election(self):
        """Test starting a custom election (POST /start_custom_election)"""
        with self.app:
            # Reset election state
            election_state.candidates = []
            election_state.votes = {}
            election_state.election_status = 'not_started'
            election_state.MAX_VOTES = None

            response = self.app.post('/start_custom_election', data={
                'number_of_custom_candidates': '3',
                'max_votes_custom': '5',
                'candidate_1': 'Alice',
                'candidate_2': 'Bob',
                'candidate_3': 'Charlie'
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            
            # Decode and unescape response data
            response_text = response.data.decode('utf-8')
            unescaped_response = html.unescape(response_text)

            # Check for the flash message in the response
            self.assertIn('Custom candidates have been added. The election has started.', unescaped_response)
            self.assertEqual(election_state.candidates, ['Alice', 'Bob', 'Charlie'])
            self.assertEqual(election_state.MAX_VOTES, 5)

    def test_results_page(self):
        """Test that the results page displays correctly."""
        with self.app:
            # Reset election state
            election_state.candidates = []
            election_state.votes = {}
            election_state.election_status = 'not_started'
            election_state.MAX_VOTES = None

            # Start an election and cast a vote
            self.app.post('/start_custom_election', data={
                'number_of_custom_candidates': '2',
                'max_votes_custom': '5',
                'candidate_1': 'Alice',
                'candidate_2': 'Bob'
            }, follow_redirects=True)
            self.app.post('/', data={'candidate': 'Alice'}, follow_redirects=True)

            # Access the results page
            response = self.app.get('/results')
            self.assertEqual(response.status_code, 200)
            response_text = response.data.decode('utf-8')
            unescaped_response = html.unescape(response_text)
            self.assertIn('Election Results', unescaped_response)
            self.assertIn('Alice', unescaped_response)
            self.assertIn('Bob', unescaped_response)

    def test_voice_vote(self):
        """Test the voice voting feature."""
        with self.app:
            # Reset election state
            election_state.candidates = []
            election_state.votes = {}
            election_state.election_status = 'not_started'
            election_state.MAX_VOTES = None

            # Set up election with two candidates
            self.app.post('/start_custom_election', data={
                'number_of_custom_candidates': '2',
                'max_votes_custom': '5',
                'candidate_1': 'Alice',
                'candidate_2': 'Bob'
            }, follow_redirects=True)

            # Simulate a voice vote with the transcript for 'Alice'
            response = self.app.post('/voice_vote', json={'transcript': 'Alice'})
            self.assertEqual(response.status_code, 200)
            response_text = response.data.decode('utf-8')
            unescaped_response = html.unescape(response_text)
            self.assertIn('Thank you! Your vote for Alice has been submitted.', unescaped_response)

            # Simulate a voice vote for an invalid transcript
            response = self.app.post('/voice_vote', json={'transcript': 'Unknown Candidate'})
            self.assertEqual(response.status_code, 400)  # Expecting a 400 for unrecognized candidate
            response_text = response.data.decode('utf-8')
            unescaped_response = html.unescape(response_text)
            self.assertIn('Candidate not recognized. Please try again.', unescaped_response)

            # Simulate a voice vote with the transcript for 'Bob'
            response = self.app.post('/voice_vote', json={'transcript': 'Bob'})
            self.assertEqual(response.status_code, 200)
            response_text = response.data.decode('utf-8')
            unescaped_response = html.unescape(response_text)
            self.assertIn('Thank you! Your vote for Bob has been submitted.', unescaped_response)

if __name__ == "__main__":
    unittest.main()