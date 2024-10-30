from extensions import db
from models.base import TimestampMixin

class Vote(db.Model, TimestampMixin):
    __tablename__ = 'votes'

    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)
    election_id = db.Column(db.Integer, db.ForeignKey('elections.id'), nullable=False)

class UserVote(db.Model, TimestampMixin):
    __tablename__ = 'user_votes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    election_id = db.Column(db.Integer, db.ForeignKey('elections.id'), nullable=False)

    __table_args__ = (db.UniqueConstraint('user_id', 'election_id', name='unique_user_election'),)