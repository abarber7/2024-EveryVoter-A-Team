import unittest
from application import app

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
            response = self.app.post('/start_custom_election', data={
                'number_of_custom_candidates': '3',
                'max_votes_custom': '5',
                'candidate_1': 'Alice',
                'candidate_2': 'Bob',
                'candidate_3': 'Charlie'
            }, follow_redirects=True)
            
            self.assertEqual(response.status_code, 200)
            with self.app.session_transaction() as session:
                flashed_messages = session['_flashes']
                self.assertIn(('info', 'Custom candidates have been added. The election has started.'), flashed_messages)

    def test_results_page(self):
        """Test that the results page displays correctly."""
        with self.app:
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
            self.assertIn(b'Election Results', response.data)
            self.assertIn(b'Alice', response.data)
            self.assertIn(b'Bob', response.data)

    
    def test_voice_vote(self):
        """Test the voice voting feature."""
        with self.app:
            # Set up election
            self.app.post('/start_custom_election', data={
                'number_of_custom_candidates': '2',
                'max_votes_custom': '5',
                'candidate_1': 'Alice',
                'candidate_2': 'Bob'
            }, follow_redirects=True)

            # Simulate a voice vote
            response = self.app.post('/voice_vote', json={'candidate': 'Alice'})
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Thank you! Your vote for Alice has been submitted.', response.data)

            # Simulate a voice vote for an invalid candidate
            response = self.app.post('/voice_vote', json={'candidate': 'InvalidCandidate'})
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Candidate not recognized. Please try again.', response.data)

if __name__ == "__main__":
    unittest.main()
