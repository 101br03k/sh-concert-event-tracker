from flask import Blueprint, request, jsonify
from datetime import datetime
from models import db, Event

api = Blueprint('api', __name__)


@api.route('/events', methods=['GET'])
def get_events():
    """Get all events with optional filtering"""
    event_type = request.args.get('type')
    status = request.args.get('status')

    query = Event.query

    if event_type:
        query = query.filter(Event.event_type == event_type)
    if status:
        query = query.filter(Event.status == status)

    events = query.order_by(Event.date.asc()).all()
    return jsonify([event.to_dict() for event in events])


@api.route('/events/<int:id>', methods=['GET'])
def get_event(id):
    """Get a single event by ID"""
    event = Event.query.get_or_404(id)
    return jsonify(event.to_dict())


@api.route('/events', methods=['POST'])
def create_event():
    """Create a new event"""
    data = request.json

    event = Event(
        name=data.get('name'),
        event_type=data.get('type', 'event'),
        venue=data.get('venue'),
        city=data.get('city'),
        date=datetime.strptime(data['date'], '%Y-%m-%d').date() if data.get('date') else None,
        time=datetime.strptime(data['time'], '%H:%M').time() if data.get('time') else None,
        price=data.get('price', 0),
        url=data.get('url'),
        source=data.get('source', 'manual'),
        companions=data.get('companions'),
        notes=data.get('notes')
    )

    db.session.add(event)
    db.session.commit()

    return jsonify(event.to_dict()), 201


@api.route('/events/<int:id>', methods=['PUT'])
def update_event(id):
    """Update an existing event"""
    event = Event.query.get_or_404(id)
    data = request.json

    event.name = data.get('name', event.name)
    event.event_type = data.get('type', event.event_type)
    event.venue = data.get('venue', event.venue)
    event.city = data.get('city', event.city)
    event.price = data.get('price', event.price)
    event.url = data.get('url', event.url)
    event.companions = data.get('companions', event.companions)
    event.notes = data.get('notes', event.notes)
    event.status = data.get('status', event.status)

    if data.get('date'):
        event.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    if data.get('time'):
        event.time = datetime.strptime(data['time'], '%H:%M').time()

    db.session.commit()

    return jsonify(event.to_dict())


@api.route('/events/<int:id>', methods=['DELETE'])
def delete_event(id):
    """Delete an event"""
    event = Event.query.get_or_404(id)
    db.session.delete(event)
    db.session.commit()

    return '', 204


@api.route('/stats', methods=['GET'])
def get_stats():
    """Get event statistics"""
    total = Event.query.count()
    by_type = db.session.query(
        Event.event_type, db.func.count(Event.id)
    ).group_by(Event.event_type).all()
    by_status = db.session.query(
        Event.status, db.func.count(Event.id)
    ).group_by(Event.status).all()

    return jsonify({
        'total': total,
        'by_type': dict(by_type),
        'by_status': dict(by_status)
    })
