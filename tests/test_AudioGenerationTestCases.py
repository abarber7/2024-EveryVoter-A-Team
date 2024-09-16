import unittest
from unittest.mock import patch, MagicMock
from application import app, db
from models.models import Election, Candidate

class AudioGenerationTestCases(unittest.TestCase):

    def setUp(self):
        """Set up the test client and push application context."""
        self.app = app.test_client()
        self.app.testing = True
        self.app_context = app.app_context()
        self.app_context.push()  # Push the application context

    def tearDown(self):
        """Pop the application context after the test."""
        self.app_context.pop()

    @patch('application.db.session')
    @patch('application.Election.query')
    def test_generate_audio_success(self, mock_election_query, mock_db_session):
        """Test successful audio generation when election has started."""

        # Mock election and candidates
        mock_election = MagicMock(spec=Election)
        mock_election.id = 1
        mock_election.status = 'ongoing'

        candidate1 = MagicMock(spec=Candidate)
        candidate1.name = 'Alice'
        candidate2 = MagicMock(spec=Candidate)
        candidate2.name = 'Bob'

        mock_election.candidates = [candidate1, candidate2]
        mock_election_query.get.return_value = mock_election

        with self.app:
            # Mock the ElevenLabs client response
            with patch('application.elevenclient.text_to_speech.convert') as mock_tts:
                mock_tts.return_value = [b'audio data']
                response = self.app.post('/generate-candidates-audio', json={'election_id': 1})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.content_type, 'audio/mpeg')

    @patch('application.Election.query')
    def test_generate_audio_no_election(self, mock_election_query):
        """Test audio generation when no election is active."""
        mock_election_query.get.return_value = None  # Simulate no election

        with self.app:
            response = self.app.post('/generate-candidates-audio', json={'election_id': 1})
            self.assertEqual(response.status_code, 400)
            self.assertIn(b'No active election', response.data)

if __name__ == "__main__":
    unittest.main()
