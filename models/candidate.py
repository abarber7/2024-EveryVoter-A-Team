from extensions import db

class Candidate(db.Model):
    __tablename__ = 'candidates'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    election_id = db.Column(db.Integer, db.ForeignKey('elections.id'), nullable=False)

    votes = db.relationship('Vote', backref='candidate', lazy=True)

    __table_args__ = (db.UniqueConstraint('election_id', 'name', name='unique_candidate_per_election'),)