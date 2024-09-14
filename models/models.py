from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Election(db.Model):
    __tablename__ = 'elections'

    id = db.Column(db.Integer, primary_key=True)
    election_type = db.Column(db.String(50), nullable=False)
    max_votes = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='ongoing')  # Options: 'ongoing', 'ended'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    candidates = db.relationship('Candidate', backref='election', lazy=True)
    votes = db.relationship('Vote', backref='election', lazy=True)

class Candidate(db.Model):
    __tablename__ = 'candidates'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    election_id = db.Column(db.Integer, db.ForeignKey('elections.id'), nullable=False)

    votes = db.relationship('Vote', backref='candidate', lazy=True)

class Vote(db.Model):
    __tablename__ = 'votes'

    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)
    election_id = db.Column(db.Integer, db.ForeignKey('elections.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

