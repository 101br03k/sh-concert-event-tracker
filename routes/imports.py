from flask import Blueprint, request, render_template, redirect, url_for
from models import db, Event
from importers.ticketswap import TicketSwapImporter
from importers.ticketmaster import TicketmasterImporter

imports = Blueprint('imports', __name__)


@imports.route('/ticketswap', methods=['POST'])
def import_ticketswap_form():
    """Import from TicketSwap via form"""
    try:
        url = request.form.get('url')
        if not url:
            return render_template('import.html', error='URL is required')
        
        importer = TicketSwapImporter(url)
        event_data = importer.parse()

        if not event_data:
            return render_template('import.html', error='Failed to parse TicketSwap URL')

        existing = Event.query.filter_by(
            source_id=event_data.get('source_id'), 
            source='ticketswap'
        ).first()
        if existing:
            return render_template('import.html', error='Event already exists')

        event = Event(
            name=event_data.get('name'),
            event_type=event_data.get('type', 'concert'),
            venue=event_data.get('venue'),
            city=event_data.get('city'),
            date=event_data.get('date'),
            time=event_data.get('time'),
            price=event_data.get('price', 0),
            currency=event_data.get('currency', 'EUR'),
            url=url,
            source='ticketswap',
            source_id=event_data.get('source_id'),
            notes=event_data.get('notes')
        )

        db.session.add(event)
        db.session.commit()
        return redirect(url_for('frontend.index'))
    except Exception as e:
        return render_template('import.html', error=str(e))


@imports.route('/ticketmaster', methods=['POST'])
def import_ticketmaster_form():
    """Import from Ticketmaster via form"""
    try:
        url = request.form.get('url')
        if not url:
            return render_template('import.html', error='URL is required')
        
        importer = TicketmasterImporter(url)
        event_data = importer.parse()

        if not event_data:
            return render_template('import.html', error='Failed to parse Ticketmaster URL')

        existing = Event.query.filter_by(
            source_id=event_data.get('source_id'), 
            source='ticketmaster'
        ).first()
        if existing:
            return render_template('import.html', error='Event already exists')

        event = Event(
            name=event_data.get('name'),
            event_type=event_data.get('type', 'concert'),
            venue=event_data.get('venue'),
            city=event_data.get('city'),
            date=event_data.get('date'),
            time=event_data.get('time'),
            price=event_data.get('price', 0),
            currency=event_data.get('currency', 'EUR'),
            url=url,
            source='ticketmaster',
            source_id=event_data.get('source_id'),
            notes=event_data.get('notes')
        )

        db.session.add(event)
        db.session.commit()
        return redirect(url_for('frontend.index'))
    except Exception as e:
        return render_template('import.html', error=str(e))


# API versions of import endpoints
@imports.route('/api/ticketswap', methods=['POST'])
def import_ticketswap_api():
    """Import from TicketSwap via API"""
    data = request.json
    url = data.get('url')

    if not url:
        return jsonify({'error': 'URL is required'}), 400

    try:
        importer = TicketSwapImporter(url)
        event_data = importer.parse()

        if not event_data:
            return jsonify({
                'error': 'Failed to parse TicketSwap URL. The page structure may have changed or the URL is invalid.'
            }), 400

        existing = Event.query.filter_by(
            source_id=event_data.get('source_id'), 
            source='ticketswap'
        ).first()
        if existing:
            return jsonify({'error': 'Event already exists', 'event': existing.to_dict()}), 409

        event = Event(
            name=event_data.get('name'),
            event_type=event_data.get('type', 'concert'),
            venue=event_data.get('venue'),
            city=event_data.get('city'),
            date=event_data.get('date'),
            time=event_data.get('time'),
            price=event_data.get('price', 0),
            currency=event_data.get('currency', 'EUR'),
            url=url,
            source='ticketswap',
            source_id=event_data.get('source_id'),
            notes=event_data.get('notes')
        )

        db.session.add(event)
        db.session.commit()

        return jsonify(event.to_dict()), 201
    except Exception as e:
        print(f"TicketSwap import error: {str(e)}")
        return jsonify({'error': f'Import failed: {str(e)}'}), 500


@imports.route('/api/ticketmaster', methods=['POST'])
def import_ticketmaster_api():
    """Import from Ticketmaster via API"""
    data = request.json
    url = data.get('url')

    if not url:
        return jsonify({'error': 'URL is required'}), 400

    try:
        importer = TicketmasterImporter(url)
        event_data = importer.parse()

        if not event_data:
            return jsonify({
                'error': 'Failed to parse Ticketmaster URL. The page structure may have changed or the URL is invalid.'
            }), 400

        existing = Event.query.filter_by(
            source_id=event_data.get('source_id'), 
            source='ticketmaster'
        ).first()
        if existing:
            return jsonify({'error': 'Event already exists', 'event': existing.to_dict()}), 409

        event = Event(
            name=event_data.get('name'),
            event_type=event_data.get('type', 'concert'),
            venue=event_data.get('venue'),
            city=event_data.get('city'),
            date=event_data.get('date'),
            time=event_data.get('time'),
            price=event_data.get('price', 0),
            currency=event_data.get('currency', 'EUR'),
            url=url,
            source='ticketmaster',
            source_id=event_data.get('source_id'),
            notes=event_data.get('notes')
        )

        db.session.add(event)
        db.session.commit()

        return jsonify(event.to_dict()), 201
    except Exception as e:
        print(f"Ticketmaster import error: {str(e)}")
        return jsonify({'error': f'Import failed: {str(e)}'}), 500
