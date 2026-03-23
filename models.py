from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Event(db.Model):
    """Event model for shows, concerts, and events"""
    __tablename__ = 'event'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)  # concert, show, event
    venue = db.Column(db.String(200))
    city = db.Column(db.String(100))
    date = db.Column(db.Date)
    time = db.Column(db.Time)
    price = db.Column(db.Float, default=0.0)
    currency = db.Column(db.String(10), default='EUR')
    url = db.Column(db.String(500))
    source = db.Column(db.String(50))  # ticketswap, ticketmaster, manual
    source_id = db.Column(db.String(100))  # Original ID from source
    companions = db.Column(db.Text)  # Comma-separated list of people
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='planned')  # planned, attended, missed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def type(self):
        """Alias for event_type for template convenience"""
        return self.event_type

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.event_type,
            'venue': self.venue,
            'city': self.city,
            'date': self.date.isoformat() if self.date else None,
            'time': self.time.isoformat() if self.time else None,
            'price': self.price,
            'currency': self.currency,
            'url': self.url,
            'source': self.source,
            'companions': self.companions,
            'notes': self.notes,
            'status': self.status
        }
