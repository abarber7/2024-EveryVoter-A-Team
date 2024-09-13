# test_integration.py

import unittest
from unittest.mock import patch, MagicMock
from io import BytesIO

from application import app, election_state

class test_Integration(unittest.TestCase):

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
        mock_get_restaurants.return_value = ['Alice\'s Diner', 'Bob\'s Burgers']

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
            self.assertIn(b'The election has started.', response.data)
            self.assertListEqual(election_state.candidates, ['Alice\'s Diner', 'Bob\'s Burgers'])
            self.assertEqual(election_state.MAX_VOTES, 3)

            # Cast votes via form submission
            response = self.app.post('/', data={'candidate': 'Alice\'s Diner'}, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Thank you! Your vote for Alice\'s Diner has been submitted.', response.data)
            self.assertEqual(election_state.votes['Alice\'s Diner'], 1)

            # Simulate a voice vote with a transcript for 'Bob's Burgers'
            with patch('application.client.audio.transcriptions.create') as mock_transcribe:
                mock_transcribe.return_value = MagicMock(text='Bob\'s Burgers')
                # Simulate sending an audio file
                data = {
                    'audio': (BytesIO(b'test audio data'), 'voice_vote.wav')
                }
                response = self.app.post('/process_audio', data=data, content_type='multipart/form-data')
                self.assertEqual(response.status_code, 200)
                self.assertIn(b'Bob\'s Burgers', response.data)

            # Process the voice vote
            response = self.app.post('/voice_vote', json={'transcript': 'Bob\'s Burgers'})
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Thank you! Your vote for Bob\'s Burgers has been submitted.', response.data)
            self.assertEqual(election_state.votes['Bob\'s Burgers'], 1)

            # Access the results page
            response = self.app.get('/results')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Election Results', response.data)
            self.assertIn(b'Alice\'s Diner', response.data)
            self.assertIn(b'Bob\'s Burgers', response.data)

    @patch('application.get_restaurant_candidates')
    def test_election_max_votes_reached(self, mock_get_restaurants):
        """Test behavior when maximum votes are reached."""
        mock_get_restaurants.return_value = ['Alice', 'Bob']

        with self.app:
            # Start an election with max_votes = 1
            self.app.post('/start_restaurant_election', data={
                'city': 'Sample City',
                'state': 'Sample State',
                'number_of_restaurants': '2',
                'max_votes': '1',
                'generate_restaurants': 'Generate Restaurants'
            }, follow_redirects=True)

            # Cast the only allowed vote
            response = self.app.post('/', data={'candidate': 'Alice'}, follow_redirects=True)
            self.assertIn(b'Thank you! Your vote for Alice has been submitted.', response.data)

            # Attempt to cast another vote
            response = self.app.post('/', data={'candidate': 'Bob'}, follow_redirects=True)
            self.assertIn(b'All votes have been cast. The election is now closed.', response.data)
            self.assertEqual(election_state.votes['Bob'], 0)

    @patch('application.get_restaurant_candidates')
    @patch('application.client.audio.transcriptions.create')
    def test_voice_vote_unrecognized_candidate(self, mock_transcribe, mock_get_restaurants):
        """Test voice voting with an unrecognized candidate."""
        mock_get_restaurants.return_value = ['Alice', 'Bob']
        mock_transcribe.return_value = MagicMock(text='Charlie')

        with self.app:
            # Start the election
            self.app.post('/start_restaurant_election', data={
                'city': 'Sample City',
                'state': 'Sample State',
                'number_of_restaurants': '2',
                'max_votes': '5',
                'generate_restaurants': 'Generate Restaurants'
            }, follow_redirects=True)

            # Simulate processing an audio file with unrecognized candidate
            data = {
                'audio': (BytesIO(b'test audio data'), 'voice_vote.wav')
            }
            response = self.app.post('/process_audio', data=data, content_type='multipart/form-data')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Charlie', response.data)

            # Process the voice vote
            response = self.app.post('/voice_vote', json={'transcript': 'Charlie'})
            self.assertEqual(response.status_code, 400)
            self.assertIn(b'Candidate not recognized. Please try again.', response.data)

    @patch('application.get_restaurant_candidates')
    def test_election_without_votes(self, mock_get_restaurants):
        """Test results page when no votes have been cast."""
        mock_get_restaurants.return_value = ['Alice', 'Bob']

        with self.app:
            # Start the election
            self.app.post('/start_restaurant_election', data={
                'city': 'Sample City',
                'state': 'Sample State',
                'number_of_restaurants': '2',
                'max_votes': '5',
                'generate_restaurants': 'Generate Restaurants'
            }, follow_redirects=True)

            # Access the results page without casting any votes
            response = self.app.get('/results')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Election Results', response.data)
            self.assertIn(b'Alice', response.data)
            self.assertIn(b'Bob', response.data)
            # Ensure that vote percentages are 0% or handled gracefully
            self.assertNotIn(b'NaN%', response.data)

if __name__ == '__main__':
    unittest.main()