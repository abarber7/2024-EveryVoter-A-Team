import unittest
from unittest.mock import patch

from application import app  # Make sure to import your Flask app

class test_AudioGenerationTestCases(unittest.TestCase):

    def setUp(self):
        """Set up the test client."""
        self.app = app.test_client()
        self.app.testing = True

    def test_generate_audio_success(self):
        """Test successful audio generation when election has started."""
        with self.app:
            # Start an election
            self.app.post('/start_custom_election', data={
                'number_of_custom_candidates': '2',
                'max_votes_custom': '5',
                'candidate_1': 'Alice',
                'candidate_2': 'Bob'
            }, follow_redirects=True)

            # Mock the ElevenLabs client response
            with patch('application.elevenclient.text_to_speech.convert') as mock_tts:
                mock_tts.return_value = [b'audio data']
                response = self.app.post('/generate-candidates-audio')
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.content_type, 'audio/mpeg')

    def test_generate_audio_no_candidates(self):
        """Test audio generation when no election has started."""
        with self.app:
            response = self.app.post('/generate-candidates-audio')
            self.assertEqual(response.status_code, 500)
            self.assertIn(b'Text generation failed', response.data)

if __name__ == "__main__":
    unittest.main()