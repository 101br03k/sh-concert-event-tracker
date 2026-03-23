import re
from datetime import datetime, date, time
from bs4 import BeautifulSoup
import requests
import json


class TicketSwapImporter:
    """Importer for TicketSwap events"""

    def __init__(self, url: str):
        self.url = url
        self.event_id = self._extract_event_id(url)

    def _extract_event_id(self, url: str) -> str:
        """Extract event ID from TicketSwap URL"""
        # TicketSwap URLs typically look like:
        # https://www.ticketswap.nl/e/event-name-12345
        match = re.search(r'/e/[^-]+-(\d+)', url)
        if match:
            return match.group(1)
        # Also try: https://www.ticketswap.nl/nl/e/event-name/12345
        match = re.search(r'/e/[^/]+/(\d+)', url)
        if match:
            return match.group(1)
        return url

    def parse(self) -> dict:
        """Parse TicketSwap event page and extract event data"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
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

            # If we couldn't extract essential info, the page structure may have changed
            if name == "Unknown Event" and not event_date:
                print("TicketSwap: Could not extract essential event data")
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
                'notes': f'Imported from TicketSwap'
            }

        except requests.exceptions.RequestException as e:
            print(f"TicketSwap: Network error - {e}")
            return None
        except Exception as e:
            print(f"Error parsing TicketSwap URL: {e}")
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
            'notes': 'Imported from TicketSwap'
        }
    
    def _extract_name(self, soup: BeautifulSoup) -> str:
        """Extract event name from page"""
        # Try various selectors for event name
        selectors = [
            'h1.event-title',
            'h1.title',
            'h1',
            '.event-name',
            '[data-testid="event-title"]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return "Unknown Event"
    
    def _extract_datetime(self, soup: BeautifulSoup) -> tuple:
        """Extract date and time from page"""
        event_date = None
        event_time = None
        
        # Look for date patterns in the page
        date_patterns = [
            r'(\d{1,2})\s+(januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)\s+(\d{4})',
            r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})',
            r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})'
        ]
        
        dutch_months = {
            'januari': 1, 'februari': 2, 'maart': 3, 'april': 4,
            'mei': 5, 'juni': 6, 'juli': 7, 'augustus': 8,
            'september': 9, 'oktober': 10, 'november': 11, 'december': 12
        }
        
        text = soup.get_text()
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()
                try:
                    if groups[1].lower() in dutch_months:
                        # Dutch format: day month year
                        day = int(groups[0])
                        month = dutch_months[groups[1].lower()]
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
            r'(\d{1,2}):(\d{2})',
            r'(\d{1,2})\s*[.:]\s*(\d{2})'
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    hour = int(match.group(1))
                    minute = int(match.group(2))
                    event_time = time(hour, minute)
                    break
                except (ValueError, IndexError):
                    continue
        
        return event_date, event_time
    
    def _extract_location(self, soup: BeautifulSoup) -> tuple:
        """Extract venue and city from page"""
        venue = None
        city = None
        
        # Look for location selectors
        location_selectors = [
            '.venue-name',
            '.location',
            '.event-location',
            '[data-testid="venue"]'
        ]
        
        for selector in location_selectors:
            element = soup.select_one(selector)
            if element:
                venue = element.get_text(strip=True)
                break
        
        # Try to extract city from address
        address_selectors = [
            '.address',
            '.event-address',
            '[data-testid="address"]'
        ]
        
        for selector in address_selectors:
            element = soup.select_one(selector)
            if element:
                address_text = element.get_text(strip=True)
                # Try to extract city from address (usually last part)
                parts = address_text.split(',')
                if len(parts) >= 2:
                    city = parts[-2].strip()
                    if not venue:
                        venue = parts[0].strip()
                break
        
        if not venue:
            # Try to find any location-related text
            text = soup.get_text()
            location_match = re.search(r'Locatie[:\s]+([^\n]+)', text, re.IGNORECASE)
            if location_match:
                venue = location_match.group(1).strip()
        
        return venue, city
    
    def _extract_price(self, soup: BeautifulSoup) -> tuple:
        """Extract price from page"""
        price = 0.0
        currency = 'EUR'
        
        # Look for price patterns
        price_patterns = [
            r'€\s*(\d+[,\.]?\d*)',
            r'EUR\s*(\d+[,\.]?\d*)',
            r'(\d+[,\.]?\d*)\s*EUR',
            r'Price[:\s]+€?\s*(\d+[,\.]?\d*)'
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
        if 'USD' in text.upper():
            currency = 'USD'
        elif 'GBP' in text.upper():
            currency = 'GBP'
        
        return price, currency
    
    def _determine_type(self, name: str) -> str:
        """Determine event type based on name"""
        name_lower = name.lower()
        
        concert_keywords = ['concert', 'live', 'band', 'dj', 'festival', 'tour', 'artist']
        show_keywords = ['show', 'theater', 'theatre', 'musical', 'play', 'comedy', 'stand-up']
        
        for keyword in concert_keywords:
            if keyword in name_lower:
                return 'concert'
        
        for keyword in show_keywords:
            if keyword in name_lower:
                return 'show'
        
        return 'event'
