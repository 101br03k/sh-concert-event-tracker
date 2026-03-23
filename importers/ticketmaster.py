import re
from datetime import datetime, date, time
from bs4 import BeautifulSoup
import requests
import json


class TicketmasterImporter:
    """Importer for Ticketmaster events"""

    def __init__(self, url: str):
        self.url = url
        self.event_id = self._extract_event_id(url)

    def _extract_event_id(self, url: str) -> str:
        """Extract event ID from Ticketmaster URL"""
        # Ticketmaster URLs typically look like:
        # https://www.ticketmaster.nl/event/artist-tickets/12345
        # https://www.ticketmaster.com/event/12345
        match = re.search(r'/event/[^/]+/(\w+)', url)
        if match:
            return match.group(1)
        match = re.search(r'/event/(\w+)', url)
        if match:
            return match.group(1)
        # Try event ID pattern
        match = re.search(r'(\d{8,})', url)
        if match:
            return match.group(1)
        return url

    def parse(self) -> dict:
        """Parse Ticketmaster event page and extract event data"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8',
                'Referer': 'https://www.google.com/'
            }
            response = requests.get(self.url, headers=headers, timeout=10, allow_redirects=True)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'lxml')

            # Try to find JSON-LD structured data first (most reliable)
            event_data = self._extract_from_json_ld(soup)
            if event_data:
                return event_data

            # Fallback to HTML parsing
            name = self._extract_name(soup)
            event_date, event_time = self._extract_datetime(soup)
            venue, city = self._extract_location(soup)
            price, currency = self._extract_price(soup)
            event_type = self._determine_type(name)

            # If we couldn't extract essential info
            if name == "Unknown Event" and not event_date:
                print("Ticketmaster: Could not extract essential event data")
                return None

            return {
                'source_id': self.event_id,
                'name': name,
                'type': event_type,
                'venue': venue,
                'city': city,
                'date': event_date,
                'time': event_time,
                'price': price,
                'currency': currency,
                'notes': f'Imported from Ticketmaster'
            }

        except requests.exceptions.RequestException as e:
            print(f"Ticketmaster: Network error - {e}")
            return None
        except Exception as e:
            print(f"Error parsing Ticketmaster URL: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _extract_from_json_ld(self, soup: BeautifulSoup) -> dict:
        """Extract event data from JSON-LD structured data"""
        try:
            script_tags = soup.find_all('script', type='application/ld+json')
            for script in script_tags:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, list):
                        for item in data:
                            event_type = item.get('@type', '')
                            # Support various event types
                            if event_type in ['Event', 'MusicEvent', 'SportsEvent', 'TheaterEvent', 'Festival', 'BusinessEvent']:
                                return self._parse_json_ld_event(item)
                    elif isinstance(data, dict):
                        event_type = data.get('@type', '')
                        if event_type in ['Event', 'MusicEvent', 'SportsEvent', 'TheaterEvent', 'Festival', 'BusinessEvent']:
                            return self._parse_json_ld_event(data)
                except (json.JSONDecodeError, TypeError):
                    continue
        except Exception as e:
            print(f"Error extracting JSON-LD: {e}")
        return None

    def _parse_json_ld_event(self, data: dict) -> dict:
        """Parse a JSON-LD event object"""
        name = data.get('name', 'Unknown Event')
        
        # Extract date/time
        event_date = None
        event_time = None
        start_date = data.get('startDate', '')
        if start_date:
            try:
                dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                event_date = dt.date()
                event_time = dt.time()
            except (ValueError, TypeError):
                pass

        # Extract venue
        venue = None
        city = None
        location = data.get('location', {})
        if isinstance(location, dict):
            venue = location.get('name', '')
            address = location.get('address', {})
            if isinstance(address, dict):
                city = address.get('addressLocality', '')
                if not venue and address.get('streetAddress'):
                    venue = address.get('streetAddress', '')

        # Extract price
        price = 0.0
        currency = 'EUR'
        offers = data.get('offers', {})
        if isinstance(offers, dict):
            if isinstance(offers.get('price'), (int, float)):
                price = float(offers['price'])
            else:
                price_str = str(offers.get('price', '0')).replace(',', '.')
                try:
                    price = float(price_str)
                except (ValueError, TypeError):
                    pass
            currency = offers.get('priceCurrency', 'EUR')

        return {
            'source_id': self.event_id,
            'name': name,
            'type': self._determine_type(name),
            'venue': venue,
            'city': city,
            'date': event_date,
            'time': event_time,
            'price': price,
            'currency': currency,
            'notes': 'Imported from Ticketmaster'
        }
    
    def _extract_name(self, soup: BeautifulSoup) -> str:
        """Extract event name from page"""
        # Try various selectors for event name
        selectors = [
            'h1[data-testid="event-title"]',
            'h1.event-title',
            'h1.title',
            'h1',
            '.event-name',
            '[data-automation="event-title"]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        # Try to find in meta tags
        meta_title = soup.find('meta', property='og:title')
        if meta_title and meta_title.get('content'):
            return meta_title['content']
        
        return "Unknown Event"
    
    def _extract_datetime(self, soup: BeautifulSoup) -> tuple:
        """Extract date and time from page"""
        event_date = None
        event_time = None
        
        # Look for structured data (JSON-LD)
        script_tags = soup.find_all('script', type='application/ld+json')
        for script in script_tags:
            try:
                import json
                data = json.loads(script.string)
                
                if isinstance(data, dict) and data.get('@type') == 'Event':
                    start_date = data.get('startDate', '')
                    if start_date:
                        dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                        event_date = dt.date()
                        event_time = dt.time()
                        return event_date, event_time
                
                # Handle array of events
                if isinstance(data, list):
                    for item in data:
                        if item.get('@type') == 'Event':
                            start_date = item.get('startDate', '')
                            if start_date:
                                dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                                event_date = dt.date()
                                event_time = dt.time()
                                return event_date, event_time
            except (json.JSONDecodeError, ValueError, AttributeError):
                continue
        
        # Look for date patterns in the page
        date_patterns = [
            r'(\d{1,2})\s+(januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)\s+(\d{4})',
            r'(\w+)\s+(\d{1,2}),?\s+(\d{4})',
            r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})',
            r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})'
        ]
        
        dutch_months = {
            'januari': 1, 'februari': 2, 'maart': 3, 'april': 4,
            'mei': 5, 'juni': 6, 'juli': 7, 'augustus': 8,
            'september': 9, 'oktober': 10, 'november': 11, 'december': 12
        }
        
        english_months = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12
        }
        
        text = soup.get_text()
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()
                try:
                    if groups[0].lower() in dutch_months:
                        # Dutch format: day month year
                        day = int(groups[0])
                        month = dutch_months[groups[0].lower()]
                        year = int(groups[2])
                        event_date = date(year, month, day)
                    elif groups[0].lower() in english_months:
                        # English format: month day year
                        month = english_months[groups[0].lower()]
                        day = int(groups[1])
                        year = int(groups[2])
                        event_date = date(year, month, day)
                    elif len(groups[0]) == 4:
                        # YYYY-MM-DD format
                        event_date = date(int(groups[0]), int(groups[1]), int(groups[2]))
                    else:
                        # DD-MM-YYYY format
                        event_date = date(int(groups[2]), int(groups[1]), int(groups[0]))
                    break
                except (ValueError, IndexError):
                    continue
        
        # Look for time patterns
        time_patterns = [
            r'(\d{1,2}):(\d{2})\s*(?:AM|PM)?',
            r'(\d{1,2})\s*[.:]\s*(\d{2})\s*(?:AM|PM)?',
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    hour = int(match.group(1))
                    minute = int(match.group(2))
                    
                    # Check for AM/PM
                    time_text = match.group(0).upper()
                    if 'PM' in time_text and hour < 12:
                        hour += 12
                    elif 'AM' in time_text and hour == 12:
                        hour = 0
                    
                    event_time = time(hour, minute)
                    break
                except (ValueError, IndexError):
                    continue
        
        return event_date, event_time
    
    def _extract_location(self, soup: BeautifulSoup) -> tuple:
        """Extract venue and city from page"""
        venue = None
        city = None
        
        # Look for structured data (JSON-LD)
        script_tags = soup.find_all('script', type='application/ld+json')
        for script in script_tags:
            try:
                import json
                data = json.loads(script.string)
                
                def extract_from_item(item):
                    nonlocal venue, city
                    location = item.get('location', {})
                    if isinstance(location, dict):
                        venue = location.get('name') or location.get('@type') == 'Place' and location.get('name')
                        address = location.get('address', {})
                        if isinstance(address, dict):
                            city = address.get('addressLocality')
                
                if isinstance(data, dict):
                    extract_from_item(data)
                elif isinstance(data, list):
                    for item in data:
                        extract_from_item(item)
                        if venue:
                            break
            except (json.JSONDecodeError, ValueError, AttributeError):
                continue
        
        # Look for location selectors
        if not venue:
            location_selectors = [
                '[data-testid="venue-name"]',
                '.venue-name',
                '.location-name',
                '.event-venue',
                '[data-automation="venue-name"]'
            ]
            
            for selector in location_selectors:
                element = soup.select_one(selector)
                if element:
                    venue = element.get_text(strip=True)
                    break
        
        # Try to extract city from address
        if not city:
            address_selectors = [
                '[data-testid="venue-address"]',
                '.venue-address',
                '.event-address',
                '.location-address'
            ]
            
            for selector in address_selectors:
                element = soup.select_one(selector)
                if element:
                    address_text = element.get_text(strip=True)
                    parts = address_text.split(',')
                    if len(parts) >= 2:
                        city = parts[-2].strip()
                        if not venue:
                            venue = parts[0].strip()
                    elif len(parts) == 1:
                        city = parts[0].strip()
                    break
        
        return venue, city
    
    def _extract_price(self, soup: BeautifulSoup) -> tuple:
        """Extract price from page"""
        price = 0.0
        currency = 'EUR'
        
        # Look for structured data (JSON-LD)
        script_tags = soup.find_all('script', type='application/ld+json')
        for script in script_tags:
            try:
                import json
                data = json.loads(script.string)
                
                def extract_price_from_item(item):
                    nonlocal price, currency
                    offers = item.get('offers', {})
                    if isinstance(offers, dict):
                        price_str = offers.get('price', '')
                        if price_str:
                            try:
                                price = float(str(price_str).replace(',', '.'))
                            except ValueError:
                                pass
                        currency = offers.get('priceCurrency', 'EUR')
                
                if isinstance(data, dict):
                    extract_price_from_item(data)
                elif isinstance(data, list):
                    for item in data:
                        extract_price_from_item(item)
            except (json.JSONDecodeError, ValueError, AttributeError):
                continue
        
        # Look for price patterns in text
        if price == 0.0:
            price_patterns = [
                r'€\s*(\d+[,\.]?\d*)',
                r'EUR\s*(\d+[,\.]?\d*)',
                r'\$(\d+[,\.]?\d*)',
                r'£(\d+[,\.]?\d*)',
                r'(\d+[,\.]?\d*)\s*EUR',
                r'Price[:\s]+€?\s*(\d+[,\.]?\d*)',
                r'From\s*€?\s*(\d+[,\.]?\d*)'
            ]
            
            text = soup.get_text()
            
            for pattern in price_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    price_str = match.group(1).replace(',', '.')
                    try:
                        price = float(price_str)
                        break
                    except ValueError:
                        continue
        
        # Check for currency
        text = soup.get_text()
        if '$' in text or 'USD' in text.upper():
            currency = 'USD'
        elif '£' in text or 'GBP' in text.upper():
            currency = 'GBP'
        
        return price, currency
    
    def _determine_type(self, name: str) -> str:
        """Determine event type based on name"""
        name_lower = name.lower()
        
        concert_keywords = ['concert', 'live', 'band', 'dj', 'festival', 'tour', 'artist', 'music']
        show_keywords = ['show', 'theater', 'theatre', 'musical', 'play', 'comedy', 'stand-up', 'circus']
        sports_keywords = ['game', 'match', 'tournament', 'championship', 'league', 'vs']
        
        for keyword in concert_keywords:
            if keyword in name_lower:
                return 'concert'
        
        for keyword in show_keywords:
            if keyword in name_lower:
                return 'show'
        
        for keyword in sports_keywords:
            if keyword in name_lower:
                return 'sports'
        
        return 'event'
