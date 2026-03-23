# Concert & Event Tracker

A full-stack Flask application for tracking shows, concerts, and events with import capabilities from major ticketing sites like TicketSwap and Ticketmaster.

## Features

- 🎵 **Track Events**: Add and manage concerts, shows, sports, and other events
- 📅 **Organized Views**: Filter events by type (Concerts, Shows, Sports, Other)
- 🔗 **Import from Ticketing Sites**: Automatically extract event details from:
  - TicketSwap
  - Ticketmaster
- 📊 **Event Statistics**: Track planned, attended, and missed events
- 🎨 **Modern UI**: Beautiful dark theme with responsive Bootstrap 5 design
- 💾 **SQLite Database**: Lightweight, file-based storage

## Tech Stack

- **Backend/Frontend**: Python + Flask (server-side rendered templates)
- **Database**: SQLite with SQLAlchemy ORM
- **Styling**: Bootstrap 5 + Bootstrap Icons
- **Containerization**: Docker + Docker Compose

## Quick Start with Docker

### Prerequisites

- Docker
- Docker Compose

### Running the Application

1. Clone or navigate to this directory

2. Start the application:
   ```bash
   docker compose up -d
   ```

3. Access the application:
   - Web Interface: http://localhost:5000

4. Stop the application:
   ```bash
   docker compose down
   ```

5. View logs:
   ```bash
   docker compose logs -f
   ```

## Manual Setup (Without Docker)

```bash
cd /path/to/project

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

The application will start on http://localhost:5000

## API Endpoints

### Events

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/events` | Get all events |
| GET | `/api/events?type=concert` | Filter events by type |
| GET | `/api/events?status=attended` | Filter events by status |
| GET | `/api/events/<id>` | Get a single event |
| POST | `/api/events` | Create a new event |
| PUT | `/api/events/<id>` | Update an event |
| DELETE | `/api/events/<id>` | Delete an event |

### Import

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/import` | Import page UI |
| POST | `/api/import/ticketswap` | Import from TicketSwap URL |
| POST | `/api/import/ticketmaster` | Import from Ticketmaster URL |

### Statistics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/stats` | Get event statistics |

## Event Data Model

```json
{
  "id": 1,
  "name": "Artist Name - Tour 2024",
  "type": "concert",
  "venue": "Arena",
  "city": "Amsterdam",
  "date": "2024-06-15",
  "time": "20:00",
  "price": 75.50,
  "currency": "EUR",
  "url": "https://...",
  "source": "ticketswap",
  "companions": "Alice, Bob",
  "notes": "Front row tickets",
  "status": "planned"
}
```

### Event Types
- `concert` - Music concerts and festivals
- `show` - Theater, comedy, and other shows
- `sports` - Sporting events
- `event` - Other events

### Event Status
- `planned` - Upcoming events
- `attended` - Events you've been to
- `missed` - Events you couldn't attend

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_PATH` | `./events.db` | Path to SQLite database |

## Project Structure

```
sh-concert-event-tracker/
├── app.py                 # Flask application factory
├── models.py              # SQLAlchemy models
├── requirements.txt       # Python dependencies
├── docker-compose.yml     # Docker Compose configuration
├── Dockerfile.backend     # Backend Docker image
├── .dockerignore          # Docker ignore file
├── routes/
│   ├── __init__.py
│   ├── frontend.py        # Web UI routes
│   ├── api.py             # REST API routes
│   └── imports.py         # Import functionality routes
├── importers/
│   ├── __init__.py
│   ├── ticketswap.py      # TicketSwap importer
│   └── ticketmaster.py    # Ticketmaster importer
├── templates/
│   ├── index.html         # Main events list
│   ├── new.html           # Add event form
│   ├── edit.html          # Edit event form
│   └── import.html        # Import page
├── public/
│   ├── styles.css         # Custom CSS
│   └── flavicon.svg       # Site favicon
└── data/                  # Database storage (created at runtime)
```

## Import Functionality

The importers extract event information from ticketing sites using JSON-LD structured data:

- Event name and type (concert/show/event/sports)
- Venue and city
- Date and time
- Price and currency
- Original ticket URL

### Supported URL Formats

**TicketSwap:**
- `https://www.ticketswap.nl/e/event-name-12345`
- `https://www.ticketswap.nl/nl/e/event-name/12345`

**Ticketmaster:**
- `https://www.ticketmaster.nl/event/artist-tickets/12345`
- `https://www.ticketmaster.com/event/12345`

### Troubleshooting Imports

1. **JavaScript-heavy sites**: These sites may use JavaScript to render content. The importers extract data from JSON-LD structured data, which is more reliable than HTML scraping.

2. **Anti-bot protection**: Sites may block automated requests. If you encounter errors:
   - Check the logs: `docker compose logs | tail -50`
   - The URL might be invalid or the event might no longer exist
   - The site may have changed its page structure

3. **Alternative**: If import fails, manually add events using the "Add Event" form.

## License

MIT
