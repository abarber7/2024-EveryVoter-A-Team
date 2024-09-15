import unittest
from application import app, db
from models.models import Election, Candidate, Vote

class ElectionIntegrationTestCase(unittest.TestCase):

    def setUp(self):
        """Set up the test client and push application context."""
        self.app = app.test_client()
        self.app.testing = True
        self.app_context = app.app_context()
        self.app_context.push()

        # Set up the database
        db.create_all()

    def tearDown(self):
        """Tear down the test and clean up the database."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_restaurant_election_workflow(self):
        """Test the workflow of setting up an election, voting, and viewing results."""
        
        # Step 1: Set up a restaurant election
        response = self.app.post('/setup_restaurant_election', data={
            'city': 'New York',
            'state': 'NY',
            'number_of_restaurants': '3',
            'max_votes': '5',
            'election_name': 'Restaurant Election'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        # Check if the election was started successfully
        self.assertIn(b"started", response.data)

        # Step 2: Verify the election exists in the database
        election = Election.query.filter_by(election_name="Restaurant Election").first()
        self.assertIsNotNone(election)
        candidates = Candidate.query.filter_by(election_id=election.id).all()
        self.assertEqual(len(candidates), 3)

        # Step 3: Submit votes for the first candidate
        for _ in range(3):
            self.app.post(f'/vote/{election.id}', data={'candidate': candidates[0].id}, follow_redirects=True)
        
        # Step 4: Submit votes for the second candidate
        for _ in range(2):
            self.app.post(f'/vote/{election.id}', data={'candidate': candidates[1].id}, follow_redirects=True)

        # Step 5: Verify the votes in the database
        votes_for_first_candidate = Vote.query.filter_by(candidate_id=candidates[0].id).count()
        votes_for_second_candidate = Vote.query.filter_by(candidate_id=candidates[1].id).count()
        total_votes = Vote.query.filter_by(election_id=election.id).count()

        self.assertEqual(votes_for_first_candidate, 3)
        self.assertEqual(votes_for_second_candidate, 2)
        self.assertEqual(total_votes, 5)

        # Step 6: Verify the results page renders correctly
        response = self.app.get(f'/results/{election.id}')
        self.assertEqual(response.status_code, 200)

        # Verify that the response contains the expected vote percentages
        response_text = response.data.decode('utf-8')
        self.assertIn("60.0%", response_text)  # 3 votes out of 5 for first candidate
        self.assertIn("40.0%", response_text)  # 2 votes out of 5 for second candidate

if __name__ == "__main__":
    unittest.main()
