
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
    start_date = db.Column(db.DateTime(timezone=True))
    end_date = db.Column(db.DateTime(timezone=True))

    candidates = db.relationship('Candidate', backref='election', lazy=True)
    votes = db.relationship('Vote', backref='election', lazy=True)
    user_votes = db.relationship('UserVote', backref='election', lazy=True)

    @property
    def is_active(self):
        now = datetime.now(timezone.utc)
        
        # If no start or end date is set, consider the election active
        if not self.start_date and not self.end_date:
            return self.status == 'ongoing'
            
        # If only start date is set
        if self.start_date and not self.end_date:
            return self.start_date <= now and self.status == 'ongoing'
            
        # If only end date is set
        if not self.start_date and self.end_date:
            return now <= self.end_date and self.status == 'ongoing'
            
        # If both dates are set
        return self.start_date <= now <= self.end_date and self.status == 'ongoing'

    @property
    def time_until_start(self):
        if not self.start_date:
            return None
            
        now = datetime.now(timezone.utc)
        if now < self.start_date:
            time_delta = self.start_date - now
            return round(time_delta.total_seconds() / 3600, 1)  # Convert to hours
        return None