from flask import Blueprint, render_template, redirect, url_for, request
from datetime import datetime
from models import db, Event

frontend = Blueprint('frontend', __name__)


@frontend.route('/')
def index():
    """Main page - show all events"""
    try:
        events = Event.query.order_by(Event.date.asc()).all()
        return render_template('index.html', events=events, active_tab='all')
    except Exception as e:
        return render_template('index.html', events=[], active_tab='all', error=str(e))


@frontend.route('/concerts')
def concerts():
    """Show only concerts"""
    try:
        events = Event.query.filter_by(event_type='concert').order_by(Event.date.asc()).all()
        return render_template('index.html', events=events, active_tab='concerts')
    except Exception as e:
        return render_template('index.html', events=[], active_tab='concerts', error=str(e))


@frontend.route('/shows')
def shows():
    """Show only shows"""
    try:
        events = Event.query.filter_by(event_type='show').order_by(Event.date.asc()).all()
        return render_template('index.html', events=events, active_tab='shows')
    except Exception as e:
        return render_template('index.html', events=[], active_tab='shows', error=str(e))


@frontend.route('/sports')
def sports():
    """Show only sports events"""
    try:
        events = Event.query.filter_by(event_type='sports').order_by(Event.date.asc()).all()
        return render_template('index.html', events=events, active_tab='sports')
    except Exception as e:
        return render_template('index.html', events=[], active_tab='sports', error=str(e))


@frontend.route('/other-events')
def other_events():
    """Show only other events"""
    try:
        events = Event.query.filter_by(event_type='event').order_by(Event.date.asc()).all()
        return render_template('index.html', events=events, active_tab='other-events')
    except Exception as e:
        return render_template('index.html', events=[], active_tab='other-events', error=str(e))


@frontend.route('/events/new')
def new_event_form():
    """Show form to create new event"""
    return render_template('new.html', event={})


@frontend.route('/events', methods=['POST'])
def create_event_form():
    """Create a new event from form"""
    try:
        event = Event(
            name=request.form.get('name'),
            event_type=request.form.get('type', 'event'),
            venue=request.form.get('venue'),
            city=request.form.get('city'),
            date=datetime.strptime(request.form.get('date'), '%Y-%m-%d').date() if request.form.get('date') else None,
            time=datetime.strptime(request.form.get('time'), '%H:%M').time() if request.form.get('time') else None,
            price=float(request.form.get('price', 0)) if request.form.get('price') else 0,
            url=request.form.get('url'),
            source='manual',
            companions=request.form.get('companions'),
            notes=request.form.get('notes'),
            status=request.form.get('status', 'planned')
        )
        db.session.add(event)
        db.session.commit()
        return redirect(url_for('frontend.index'))
    except Exception as e:
        return render_template('new.html', event=request.form, error=str(e))


@frontend.route('/events/<int:id>/edit', methods=['GET', 'POST'])
def edit_event_form(id):
    """Show form to edit event or update it"""
    try:
        event = Event.query.get_or_404(id)
        
        if request.method == 'POST':
            event.name = request.form.get('name', event.name)
            event.event_type = request.form.get('type', event.event_type)
            event.venue = request.form.get('venue', event.venue)
            event.city = request.form.get('city', event.city)
            event.price = float(request.form.get('price', event.price)) if request.form.get('price') else event.price
            event.url = request.form.get('url', event.url)
            event.companions = request.form.get('companions', event.companions)
            event.notes = request.form.get('notes', event.notes)
            event.status = request.form.get('status', event.status)

            date_str = request.form.get('date', '').strip()
            time_str = request.form.get('time', '').strip()
            
            if date_str:
                event.date = datetime.strptime(date_str, '%Y-%m-%d').date()
            if time_str:
                # Handle both HH:MM and HH:MM:SS formats
                try:
                    event.time = datetime.strptime(time_str, '%H:%M').time()
                except ValueError:
                    event.time = datetime.strptime(time_str, '%H:%M:%S').time()

            db.session.commit()
            return redirect(url_for('frontend.index'))
        
        return render_template('edit.html', event=event)
    except Exception as e:
        import traceback
        print(f"Error updating event: {traceback.format_exc()}")
        event = Event.query.get(id)
        return render_template('edit.html', event=event, error=str(e))


@frontend.route('/events/<int:id>/delete', methods=['POST'])
def delete_event_form(id):
    """Delete event from form"""
    try:
        event = Event.query.get_or_404(id)
        db.session.delete(event)
        db.session.commit()
    except Exception as e:
        pass
    return redirect(url_for('frontend.index'))


@frontend.route('/import')
def import_page():
    """Import page"""
    return render_template('import.html')
