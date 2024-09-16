from datetime import datetime, timezone
from application import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class User(db.Model, UserMixin):  # Inherit from UserMixin
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)

    # Flask-Login expects this to be defined
    def is_active(self):
        return True  # All users are active by default

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Election(db.Model):
    __tablename__ = 'elections'

    id = db.Column(db.Integer, primary_key=True)
    election_name = db.Column(db.String(100), nullable=False, unique=True)  # Unique election name
    election_type = db.Column(db.String(50), nullable=False)
    max_votes = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='ongoing')  # Options: 'ongoing', 'ended'
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))  # Timezone-aware datetime

    candidates = db.relationship('Candidate', backref='election', lazy=True)
    votes = db.relationship('Vote', backref='election', lazy=True)
    user_votes = db.relationship('UserVote', backref='election', lazy=True)  # Track which users have voted

class Candidate(db.Model):
    __tablename__ = 'candidates'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    election_id = db.Column(db.Integer, db.ForeignKey('elections.id'), nullable=False)

    votes = db.relationship('Vote', backref='candidate', lazy=True)

    __table_args__ = (db.UniqueConstraint('election_id', 'name', name='unique_candidate_per_election'),)

class Vote(db.Model):
    __tablename__ = 'votes'

    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)
    election_id = db.Column(db.Integer, db.ForeignKey('elections.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))  # Timezone-aware datetime

class UserVote(db.Model):
    __tablename__ = 'user_votes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    election_id = db.Column(db.Integer, db.ForeignKey('elections.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))  # Timezone-aware datetime

    # Ensure a user can vote only once per election
    __table_args__ = (db.UniqueConstraint('user_id', 'election_id', name='unique_user_election'),)
