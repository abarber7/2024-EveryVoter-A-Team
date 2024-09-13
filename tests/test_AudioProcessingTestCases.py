# test_audio_processing.py

import unittest
from unittest.mock import patch, MagicMock
from io import BytesIO

from application import app

class AudioProcessingTestCases(unittest.TestCase):

    def setUp(self):
        """Set up the test client."""
        self.app = app.test_client()
        self.app.testing = True

    @patch('application.client.audio.transcriptions.create')
    def test_process_audio_success(self, mock_transcribe):
        """Test processing a valid audio file."""
        # Mock the OpenAI transcription response
        mock_transcribe.return_value = MagicMock(text='Alice')

        # Simulate sending an audio file
        data = {
            'audio': (BytesIO(b'test audio data'), 'voice_vote.wav')
        }
        response = self.app.post('/process_audio', data=data, content_type='multipart/form-data')

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Alice', response.data)

    def test_process_audio_no_file(self):
        """Test processing without providing an audio file."""
        response = self.app.post('/process_audio', data={}, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'No audio file provided', response.data)

if __name__ == '__main__':
    unittest.main()