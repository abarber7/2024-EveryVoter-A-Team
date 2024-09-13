# test_integration.py

import unittest
from unittest.mock import patch, MagicMock
from io import BytesIO
import html  # Import html module to unescape HTML entities

from application import app, election_state

class IntegrationTestCase(unittest.TestCase):

    def setUp(self):
        """Set up the test client and reset election state."""
        self.app = app.test_client()
        self.app.testing = True

        # Reset the election state before each test
        election_state.candidates = []
        election_state.votes = {}
        election_state.election_status = 'not_started'
        election_state.MAX_VOTES = None
        election_state.restaurant_election_started = False

    @patch('application.get_restaurant_candidates')
    def test_full_election_workflow(self, mock_get_restaurants):
        """Simulate the entire election process."""
        # Mock the GPT-4 response for restaurant candidates
        mock_get_restaurants.return_value = ["Alice's Diner", "Bob's Burgers"]

        with self.app:
            # Start a restaurant election
            response = self.app.post('/start_restaurant_election', data={
                'city': 'Sample City',
                'state': 'Sample State',
                'number_of_restaurants': '2',
                'max_votes': '3',
                'generate_restaurants': 'Generate Restaurants'
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)

            # Decode and unescape response data
            response_text = response.data.decode('utf-8')
            unescaped_response = html.unescape(response_text)

            self.assertIn("Restaurants have been generated. The election has started.", unescaped_response)
            self.assertListEqual(election_state.candidates, ["Alice's Diner", "Bob's Burgers"])
            self.assertEqual(election_state.MAX_VOTES, 3)

            # Cast votes via form submission
            response = self.app.post('/', data={'candidate': "Alice's Diner"}, follow_redirects=True)
            self.assertEqual(response.status_code, 200)

            # Decode and unescape response data
            response_text = response.data.decode('utf-8')
            unescaped_response = html.unescape(response_text)

            self.assertIn("Thank you! Your vote for Alice's Diner has been submitted.", unescaped_response)
            self.assertEqual(election_state.votes["Alice's Diner"], 1)

            # Simulate a voice vote with a transcript for 'Bob's Burgers'
            with patch('application.client.audio.transcriptions.create') as mock_transcribe:
                mock_transcribe.return_value = MagicMock(text="Bob's Burgers")
                # Simulate sending an audio file
                data = {
                    'audio': (BytesIO(b'test audio data'), 'voice_vote.wav')
                }
                response = self.app.post('/process_audio', data=data, content_type='multipart/form-data')
                self.assertEqual(response.status_code, 200)

                # Decode and unescape response data
                response_text = response.data.decode('utf-8')
                unescaped_response = html.unescape(response_text)

                self.assertIn("Bob's Burgers", unescaped_response)

            # Process the voice vote
            response = self.app.post('/voice_vote', json={'transcript': "Bob's Burgers"}, follow_redirects=True)
            self.assertEqual(response.status_code, 200)

            # Decode and unescape response data
            response_text = response.data.decode('utf-8')
            unescaped_response = html.unescape(response_text)

            self.assertIn("Thank you! Your vote for Bob's Burgers has been submitted.", unescaped_response)
            self.assertEqual(election_state.votes["Bob's Burgers"], 1)

            # Access the results page
            response = self.app.get('/results')
            self.assertEqual(response.status_code, 200)
            response_text = response.data.decode('utf-8')
            unescaped_response = html.unescape(response_text)
            self.assertIn('Election Results', unescaped_response)
            self.assertIn("Alice's Diner", unescaped_response)
            self.assertIn("Bob's Burgers", unescaped_response)

    @patch('application.get_restaurant_candidates')
    def test_election_max_votes_reached(self, mock_get_restaurants):
        """Test behavior when maximum votes are reached."""
        mock_get_restaurants.return_value = ['Alice', 'Bob']

        with self.app:
            # Start an election with max_votes = 1
            response = self.app.post('/start_restaurant_election', data={
                'city': 'Sample City',
                'state': 'Sample State',
                'number_of_restaurants': '2',
                'max_votes': '1',
                'generate_restaurants': 'Generate Restaurants'
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)

            # Cast the only allowed vote
            response = self.app.post('/', data={'candidate': 'Alice'}, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            response_text = response.data.decode('utf-8')
            unescaped_response = html.unescape(response_text)
            self.assertIn('Thank you! Your vote for Alice has been submitted.', unescaped_response)
            self.assertEqual(election_state.votes['Alice'], 1)

            # Attempt to cast another vote
            response = self.app.post('/', data={'candidate': 'Bob'}, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            response_text = response.data.decode('utf-8')
            unescaped_response = html.unescape(response_text)
            self.assertIn('All votes have been cast. The election is now closed.', unescaped_response)
            self.assertEqual(election_state.votes.get('Bob', 0), 0)

    @patch('application.get_restaurant_candidates')
    @patch('application.client.audio.transcriptions.create')
    def test_voice_vote_unrecognized_candidate(self, mock_transcribe, mock_get_restaurants):
        """Test voice voting with an unrecognized candidate."""
        mock_get_restaurants.return_value = ['Alice', 'Bob']
        mock_transcribe.return_value = MagicMock(text='Charlie')

        with self.app:
            # Start the election
            response = self.app.post('/start_restaurant_election', data={
                'city': 'Sample City',
                'state': 'Sample State',
                'number_of_restaurants': '2',
                'max_votes': '5',
                'generate_restaurants': 'Generate Restaurants'
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)

            # Simulate processing an audio file with unrecognized candidate
            data = {
                'audio': (BytesIO(b'test audio data'), 'voice_vote.wav')
            }
            response = self.app.post('/process_audio', data=data, content_type='multipart/form-data')
            self.assertEqual(response.status_code, 200)

            # Decode and unescape response data
            response_text = response.data.decode('utf-8')
            unescaped_response = html.unescape(response_text)
            self.assertIn('Charlie', unescaped_response)

            # Process the voice vote
            response = self.app.post('/voice_vote', json={'transcript': 'Charlie'}, follow_redirects=True)
            self.assertEqual(response.status_code, 400)
            response_text = response.data.decode('utf-8')
            unescaped_response = html.unescape(response_text)
            self.assertIn('Candidate not recognized. Please try again.', unescaped_response)

    @patch('application.get_restaurant_candidates')
    def test_election_without_votes(self, mock_get_restaurants):
        """Test results page when no votes have been cast."""
        mock_get_restaurants.return_value = ['Alice', 'Bob']

        with self.app:
            # Start the election
            response = self.app.post('/start_restaurant_election', data={
                'city': 'Sample City',
                'state': 'Sample State',
                'number_of_restaurants': '2',
                'max_votes': '5',
                'generate_restaurants': 'Generate Restaurants'
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)

            # Access the results page without casting any votes
            response = self.app.get('/results')
            self.assertEqual(response.status_code, 200)
            response_text = response.data.decode('utf-8')
            unescaped_response = html.unescape(response_text)
            self.assertIn('Election Results', unescaped_response)
            self.assertIn('Alice', unescaped_response)
            self.assertIn('Bob', unescaped_response)
            # Ensure that vote percentages are 0% or handled gracefully
            self.assertNotIn('NaN%', unescaped_response)

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
                'max_votes_custom': '10',
                'candidate_1': 'Candidate A',
                'candidate_2': 'Candidate B',
                'candidate_3': 'Candidate C'
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)

            # Decode and unescape response data
            response_text = response.data.decode('utf-8')
            unescaped_response = html.unescape(response_text)

            # Check for the flash message
            self.assertIn('Custom candidates have been added. The election has started.', unescaped_response)
            self.assertEqual(election_state.candidates, ['Candidate A', 'Candidate B', 'Candidate C'])
            self.assertEqual(election_state.MAX_VOTES, 10)

if __name__ == '__main__':
    unittest.main()