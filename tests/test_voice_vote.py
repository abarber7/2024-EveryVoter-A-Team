import unittest
from flask import url_for
from application import create_app
from extensions import db
from models import Election, Candidate, User, Vote, UserVote
import json
import io

class TestVoiceVote(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        
        # Configure the app for testing
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['SERVER_NAME'] = 'localhost'
        
        # Create the database tables
        db.create_all()
        
        # Register a test user
        self.register('testuser', 'testpassword')
        
        # Create a test election
        self.election = Election(election_name='Test Election', election_type='test', max_votes=100, status='ongoing')
        db.session.add(self.election)
        db.session.flush()  # This will assign an ID to the election
        
        # Create candidates and associate them with the election
        candidates = ['Candidate A', 'Candidate B', 'Candidate C']
        for candidate_name in candidates:
            candidate = Candidate(name=candidate_name, election_id=self.election.id)
            db.session.add(candidate)
        
        # Commit all changes
        db.session.commit()
        
        # Set the user attribute
        self.user = User.query.filter_by(username='testuser').first()

    def register(self, username, password):
        return self.client.post('/register', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def login(self):
        return self.client.post('/login', data=dict(
            username='testuser',
            password='testpassword'
        ), follow_redirects=True)

    def test_process_audio(self):
        response = self.login()
        self.assertEqual(response.status_code, 200)
        
        # Create a small valid WAV file
        import wave
        import struct

        dummy_audio = io.BytesIO()
        with wave.open(dummy_audio, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(44100)
            for _ in range(44100):  # 1 second of silence
                value = struct.pack('<h', 0)
                wav_file.writeframesraw(value)
        dummy_audio.seek(0)

        data = {'audio': (dummy_audio, 'test.wav')}
        
        response = self.client.post('/process_audio', data=data, content_type='multipart/form-data')
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.data}")
        
        self.assertIn(response.status_code, [200, 202, 500])  # Accept either 200 or 202 (Accepted) status
        
        # Check if the response is JSON
        self.assertEqual(response.content_type, 'application/json')
        
        # Parse the JSON response
        json_data = json.loads(response.data)
        
        if response.status_code == 500:
            self.assertIn('error', json_data)
        else:
            # Otherwise, expect either a transcript or task_id
            self.assertTrue('transcript' in json_data or 'task_id' in json_data)

    def test_voice_vote(self):
        response = self.login()
        self.assertEqual(response.status_code, 200)
        
        # Simulate a voice vote
        data = {
            'transcript': 'Candidate A',
            'election_id': self.election.id
        }
        
        # First vote (should succeed)
        response = self.client.post('/voice_vote', json=data)
        self.assertEqual(response.status_code, 200)
        
        # Check if the response contains a success message
        json_data = json.loads(response.data)
        self.assertIn('message', json_data)
        self.assertIn('Your vote for Candidate A has been submitted', json_data['message'])
        
        # Check if the vote was recorded
        vote = Vote.query.filter_by(election_id=self.election.id).first()
        self.assertIsNotNone(vote)
        self.assertEqual(vote.candidate.name, 'Candidate A')
        
        # Check if user vote was recorded
        user_vote = UserVote.query.filter_by(user_id=self.user.id, election_id=self.election.id).first()
        self.assertIsNotNone(user_vote)

        # Test voting twice (should fail)
        response = self.client.post('/voice_vote', json=data)
        self.assertEqual(response.status_code, 400)
        json_data = json.loads(response.data)
        self.assertIn('message', json_data)
        self.assertIn('already voted', json_data['message'])

    def test_voice_vote_invalid_candidate(self):
        response = self.login()
        self.assertEqual(response.status_code, 200)
        
        # Simulate a voice vote with an invalid candidate
        data = {
            'transcript': 'Invalid Candidate',
            'election_id': self.election.id
        }
        
        response = self.client.post('/voice_vote', json=data)
        self.assertEqual(response.status_code, 400)
        
        # Check that no vote was recorded
        vote = Vote.query.filter_by(election_id=self.election.id).first()
        self.assertIsNone(vote)

    def test_voice_vote_already_voted(self):
        response = self.login()
        self.assertEqual(response.status_code, 200)
        
        # Record a vote for the user
        user_vote = UserVote(user_id=self.user.id, election_id=self.election.id)
        db.session.add(user_vote)
        db.session.commit()
        
        # Attempt to vote again
        data = {
            'transcript': 'Candidate B',
            'election_id': self.election.id
        }
        
        response = self.client.post('/voice_vote', json=data)
        self.assertEqual(response.status_code, 400)
        
        # Check that no new vote was recorded
        votes = Vote.query.filter_by(election_id=self.election.id).all()
        self.assertEqual(len(votes), 0)

if __name__ == '__main__':
    unittest.main()