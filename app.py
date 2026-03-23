import os
from flask import Flask
from flask_cors import CORS
from datetime import datetime

from models import db, Event
from routes import frontend, api, imports


def create_app():
    """Application factory for creating Flask app"""
    app = Flask(__name__, static_folder='public', static_url_path='/static')
    CORS(app)

    # Database configuration
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.environ.get('DATABASE_PATH', os.path.join(basedir, 'events.db'))
    os.makedirs(os.path.dirname(db_path), exist_ok=True) if os.path.dirname(db_path) else None
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    db.init_app(app)

    # Create tables
    with app.app_context():
        db.create_all()

    # Register custom template filters
    @app.template_filter('format_date')
    def format_date_filter(date_obj, format_type='short'):
        """Format date for templates"""
        if not date_obj:
            return ''
        if isinstance(date_obj, str):
            try:
                date_obj = datetime.strptime(date_obj, '%Y-%m-%d').date()
            except ValueError:
                return date_obj
        if format_type == 'short':
            weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            return f"{weekdays[date_obj.weekday()]}, {date_obj.strftime('%b %d, %Y')}"
        return date_obj.strftime('%b %d, %Y')

    @app.template_filter('format_time')
    def format_time_filter(time_obj, format_type='short'):
        """Format time for templates"""
        if not time_obj:
            return ''
        if isinstance(time_obj, str):
            try:
                time_obj = datetime.strptime(time_obj, '%H:%M:%S').time()
            except ValueError:
                try:
                    time_obj = datetime.strptime(time_obj, '%H:%M').time()
                except ValueError:
                    return time_obj
        return time_obj.strftime('%H:%M')

    # Register blueprints
    app.register_blueprint(frontend)
    app.register_blueprint(api, url_prefix='/api')
    app.register_blueprint(imports, url_prefix='/import')

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
