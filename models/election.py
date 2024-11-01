
from extensions import db
from models.base import TimestampMixin
from datetime import datetime, timezone

class Election(db.Model, TimestampMixin):
    __tablename__ = 'elections'

    id = db.Column(db.Integer, primary_key=True)
    election_name = db.Column(db.String(100), nullable=False, unique=True)
    election_type = db.Column(db.String(50), nullable=False)
    max_votes = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='ongoing')
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)

    candidates = db.relationship('Candidate', backref='election', lazy=True)
    votes = db.relationship('Vote', backref='election', lazy=True)
    user_votes = db.relationship('UserVote', backref='election', lazy=True)

    @property
    def is_active(self):
        now = datetime.now(timezone.utc)
        
        # If no date range is set, consider it always active when status is 'ongoing'
        if not self.start_date and not self.end_date:
            return self.status == 'ongoing'
            
        # If date range is set, check if current time is within range
        if self.start_date and self.end_date:
            return (self.start_date <= now <= self.end_date and 
                   self.status == 'ongoing')
            
        return False

    @property
    def time_until_start(self):
        if not self.start_date or self.is_active:
            return None
        
        now = datetime.now(timezone.utc)
        if now < self.start_date:
            delta = self.start_date - now
            hours = delta.total_seconds() / 3600
            return round(hours, 1)
        return None