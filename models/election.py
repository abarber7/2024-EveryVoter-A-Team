from extensions import db
from models.base import TimestampMixin

class Election(db.Model, TimestampMixin):
    __tablename__ = 'elections'

    id = db.Column(db.Integer, primary_key=True)
    election_name = db.Column(db.String(100), nullable=False, unique=True)
    election_type = db.Column(db.String(50), nullable=False)
    max_votes = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='ongoing')

    candidates = db.relationship('Candidate', backref='election', lazy=True)
    votes = db.relationship('Vote', backref='election', lazy=True)
    user_votes = db.relationship('UserVote', backref='election', lazy=True)