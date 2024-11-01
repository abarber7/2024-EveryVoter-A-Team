from models import Election, Candidate
class ElectionService:
    def __init__(self, model, db):
        """Initialize the ElectionService with GPT-4 model and database session."""
        self.model = model
        self.db = db

    # Helper function for generating GPT-4 introductions
    def generate_gpt4_text_introduction(self, election):
        introductions = []
        for index, candidate in enumerate(election.candidates, start=1):
            gpt_text = self.model.invoke(f"""In a quirky and enthusiastic tone, welcome {candidate.name} to a show in a few words. 
                                            Example:
                                            Introducing first, the animated and lively Tony Hawk!
                                            Introducing second, the wonderful and endearing Mariah Carey!
                                            Introduce them as follows:
                                            Introducing {self.ordinal(index)}, the animated and lively Tony Hawk!""")
            introductions.append(gpt_text.content)
        return introductions

    # Helper function that returns ordinal of a number
    def ordinal(self, n):
        if isinstance(n, int):
            if 10 <= n % 100 <= 20:
                suffix = 'th'
            else:
                suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
            return f"{n}{suffix}"
        else:
            raise ValueError(f"Expected integer, got {type(n)}")

    # Generate restaurant candidates using GPT-4
    def get_restaurant_candidates(self, number_of_restaurants, city, state):
        prompt = f"Generate {number_of_restaurants} unique restaurant names in {city}, {state}."
        response = self.model.invoke(prompt)
        return response.content.strip().split("\n")[:number_of_restaurants]

    # Start a new election
    def start_election(self, candidates, max_votes, election_type, election_name, start_date=None, end_date=None):
        election = Election(
            election_name=election_name,
            election_type=election_type,
            max_votes=max_votes,
            start_date=start_date,
            end_date=end_date
        )
        
        self.db.session.add(election)
        self.db.session.commit()

        for candidate_name in candidates:
            candidate = Candidate(name=candidate_name.strip(), election_id=election.id)
            self.db.session.add(candidate)
        self.db.session.commit()

        return election.id
