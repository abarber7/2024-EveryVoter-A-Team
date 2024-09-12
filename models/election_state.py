class ElectionState:
    """
    Manages the state of the restaurant election process, including votes, candidates, and election status.
    """
    def __init__(self):
        self.votes = {}
        self.candidates = []
        self.election_status = 'not_started'
        self.MAX_VOTES = None
        self.restaurant_election_started = False

    def reset(self):
        """
        Resets the election state to initial values.
        """
        self.votes = {}
        self.candidates = []
        self.election_status = 'not_started'
        self.MAX_VOTES = None
        self.restaurant_election_started = False