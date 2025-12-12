"""
Deadline and calendar scraper for Oakton Community College.
Extracts important dates, deadlines, and calendar events.
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import re
from datetime import datetime, timedelta
import time


class DeadlineScraper:
    """Scrapes deadlines and important dates from Oakton website."""
    
    BASE_URL = "https://www.oakton.edu"
    IMPORTANT_DATES_URL = "https://www.oakton.edu/academics/important-dates.php"
    
    def __init__(self, delay: float = 1.0):
        """Initialize deadline scraper."""
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def parse_date(self, date_str: str) -> Optional[datetime]:
        """
        Parse various date formats from Oakton website.
        
        Examples:
        - "January 15, 2024"
        - "Jan 15"
        - "01/15/2024"
        - "January 15"
        """
        if not date_str:
            return None
        
        date_str = date_str.strip()
        
        # Common date formats
        formats = [
            "%B %d, %Y",      # January 15, 2024
            "%b %d, %Y",      # Jan 15, 2024
            "%B %d",          # January 15 (no year - assume current)
            "%b %d",          # Jan 15
            "%m/%d/%Y",       # 01/15/2024
            "%m/%d/%y",       # 01/15/24
            "%Y-%m-%d",       # 2024-01-15
            "%B %d, %Y %I:%M %p",  # January 15, 2024 11:59 PM
        ]
        
        current_year = datetime.now().year
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                # If no year was parsed, use current year
                if dt.year == 1900:
                    dt = dt.replace(year=current_year)
                return dt
            except ValueError:
                continue
        
        return None
    
    def extract_deadlines(self) -> List[Dict]:
        """
        Scrape important dates page and extract deadlines.
        
        Note: The actual dates are loaded via JavaScript widgets (localist-widget),
        so we extract accordion section metadata and try to fetch widget data.
        
        Returns:
            List of deadline dictionaries with date, description, category, etc.
        """
        try:
            print(f"Scraping deadlines from: {self.IMPORTANT_DATES_URL}")
            response = self.session.get(self.IMPORTANT_DATES_URL, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            
            deadlines = []
            
            # Oakton uses accordion sections with JavaScript-loaded widgets
            # Extract accordion sections and their categories
            accordion_sections = soup.find_all('section', class_=re.compile(r'accordion', re.I))
            
            # Also check for sections with id starting with 'oakton-section'
            all_sections = soup.find_all('section', id=re.compile(r'oakton-section', re.I))
            for section in all_sections:
                if section not in accordion_sections:
                    accordion_sections.append(section)
            
            for section in accordion_sections:
                section_id = section.get('id', '')
                section_title = ''
                
                # Get section title (h2)
                h2 = section.find('h2')
                if h2:
                    section_title = h2.get_text(strip=True)
                
                # Find all accordion rows (accRow class)
                accordion_rows = section.find_all('div', class_='accRow')
                
                for row in accordion_rows:
                    # Get the label (category/term name)
                    label = row.find('label')
                    if not label:
                        continue
                    
                    category_name = label.get_text(strip=True)
                    
                    # Get the content div
                    content_div = row.find('div', class_='wysiwygContent')
                    if not content_div:
                        continue
                    
                    # Look for localist widget divs - these contain the actual calendar data
                    widget_divs = content_div.find_all('div', class_='localist-widget')
                    
                    for widget_div in widget_divs:
                        widget_id = widget_div.get('id', '')
                        
                        # Try to find the script that loads this widget
                        # Script is usually a sibling or next element
                        script = content_div.find_next('script', src=re.compile(r'events\.oakton\.edu'))
                        if script:
                            widget_url = script.get('src', '')
                            if not widget_url.startswith('http'):
                                widget_url = 'https:' + widget_url if widget_url.startswith('//') else 'https://events.oakton.edu' + widget_url
                            
                            # Try to fetch widget data directly
                            widget_data = self._fetch_widget_data(widget_url, widget_id)
                            if widget_data:
                                for item in widget_data:
                                    item['category'] = self.categorize_deadline(category_name)
                                    item['section'] = section_title
                                    item['url'] = self.IMPORTANT_DATES_URL
                                    item['scraped_at'] = datetime.utcnow().isoformat()
                                    deadlines.extend([item])
                    
                    # Fallback: Look for any static date patterns in the content
                    content_text = content_div.get_text()
                    static_dates = self._extract_static_dates(content_text, category_name)
                    for date_item in static_dates:
                        date_item['section'] = section_title
                    deadlines.extend(static_dates)
            
            # Also scan the entire page for any static dates as a fallback
            page_text = soup.get_text()
            page_dates = self._extract_static_dates(page_text, 'general')
            deadlines.extend(page_dates)
            
            # Also check for any tables as fallback
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows[1:]:  # Skip header row
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        date_text = cells[0].get_text(strip=True)
                        description = cells[1].get_text(strip=True)
                        
                        deadline_date = self.parse_date(date_text)
                        if deadline_date:
                            category = self.categorize_deadline(description)
                            deadlines.append({
                                'date': deadline_date.isoformat(),
                                'description': description,
                                'category': category,
                                'date_text': date_text,
                                'url': self.IMPORTANT_DATES_URL,
                                'scraped_at': datetime.utcnow().isoformat()
                            })
            
            # Remove duplicates (same date + similar description)
            seen = set()
            unique_deadlines = []
            for deadline in deadlines:
                key = (deadline.get('date', ''), deadline.get('description', '')[:50])
                if key and key not in seen:
                    seen.add(key)
                    unique_deadlines.append(deadline)
            
            return unique_deadlines
            
        except Exception as e:
            print(f"Error scraping deadlines: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _fetch_widget_data(self, widget_url: str, widget_id: str) -> List[Dict]:
        """
        Try to fetch data from Localist widget URL.
        Widgets are loaded from events.oakton.edu with calendar data.
        """
        deadlines = []
        
        try:
            # Widget URLs look like:
            # https://events.oakton.edu/widget/view?schools=oakton&types=47497454252821&days=365&num=50&experience=inperson&container=localist-widget-32941586&template=academic-calendar-text
            
            # Try to fetch the widget content directly
            # Remove the container parameter as it's not needed for API calls
            api_url = widget_url.split('&container=')[0] if '&container=' in widget_url else widget_url
            api_url = api_url.replace('&template=academic-calendar-text', '')  # Remove template param
            
            try:
                response = self.session.get(api_url, timeout=10, headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Referer': self.IMPORTANT_DATES_URL
                })
                
                if response.status_code == 200:
                    # Try to parse widget HTML response
                    widget_soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Look for structured date elements in the widget
                    # Localist widgets often have specific structures
                    date_elements = widget_soup.find_all(['div', 'span', 'p', 'li'], 
                                                         class_=re.compile(r'date|event|deadline', re.I))
                    
                    for elem in date_elements:
                        elem_text = elem.get_text(separator=' ', strip=True)
                        if elem_text:
                            # Try to extract dates from this element
                            dates_in_elem = self._extract_static_dates(elem_text, '')
                            deadlines.extend(dates_in_elem)
                    
                    # Fallback: Extract all text and look for dates
                    widget_text = widget_soup.get_text(separator=' ', strip=True)
                    # Clean up the text
                    import html
                    widget_text = html.unescape(widget_text)
                    widget_text = re.sub(r'<[^>]+>', ' ', widget_text)  # Remove any remaining HTML tags
                    widget_text = re.sub(r'\s+', ' ', widget_text).strip()
                    
                    # Look for date patterns in widget response
                    dates_in_widget = self._extract_static_dates(widget_text, '')
                    deadlines.extend(dates_in_widget)
                    
            except Exception as fetch_error:
                # Widget API might be CORS-protected or require authentication
                pass
            
        except Exception as e:
            print(f"Note: Could not fetch widget data for {widget_id}: {e}")
        
        return deadlines
    
    def _extract_static_dates(self, text: str, category: str) -> List[Dict]:
        """Extract any date patterns from static text."""
        import html
        
        deadlines = []
        
        # Clean HTML entities from text first
        text = html.unescape(text)
        # Remove HTML tags if any
        text = re.sub(r'<[^>]+>', ' ', text)
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Look for date patterns
        date_pattern = re.compile(
            r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:,\s+\d{4})?',
            re.IGNORECASE
        )
        
        # Also look for short date formats
        short_date_pattern = re.compile(
            r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2}(?:,\s+\d{4})?',
            re.IGNORECASE
        )
        
        # Also MM/DD/YYYY format
        numeric_date_pattern = re.compile(r'\d{1,2}/\d{1,2}/\d{4}')
        
        # Find all unique matches
        all_matches = set(date_pattern.findall(text) + short_date_pattern.findall(text) + numeric_date_pattern.findall(text))
        
        for match in all_matches:
            deadline_date = self.parse_date(match)
            if deadline_date:
                # Try to extract description context around the date
                desc = category if category else 'Important date'
                # Look for text near the date in the original text
                match_pos = text.find(match)
                if match_pos >= 0:
                    context_start = max(0, match_pos - 100)
                    context_end = min(len(text), match_pos + len(match) + 150)
                    context = text[context_start:context_end].strip()
                    
                    # Aggressively clean HTML artifacts
                    context = re.sub(r'<[^>]+>', ' ', context)  # Remove HTML tags
                    context = re.sub(r'\\u[0-9a-fA-F]{4}', '', context)  # Remove Unicode escapes
                    context = re.sub(r'&[a-z]+;', ' ', context)  # Remove HTML entities
                    context = re.sub(r'\s+', ' ', context).strip()  # Normalize whitespace
                    
                    # Try to find meaningful text (at least 10 chars, not just symbols)
                    if len(context) > len(match) + 10:
                        # Try to extract sentence or phrase containing the date
                        words = context.split()
                        try:
                            match_idx = words.index(match.split()[0])  # Find first word of date
                            # Get 5 words before and 10 words after
                            start_idx = max(0, match_idx - 5)
                            end_idx = min(len(words), match_idx + 15)
                            desc = ' '.join(words[start_idx:end_idx])
                        except (ValueError, IndexError):
                            desc = context[:200]
                    
                # Ensure description isn't just the date or HTML artifacts
                # Remove common HTML artifacts and unicode escapes
                desc_clean = desc
                desc_clean = re.sub(r'\\u[0-9a-fA-F]{4}', '', desc_clean)  # Remove \uXXXX
                desc_clean = re.sub(r'[<>]', '', desc_clean)  # Remove < >
                desc_clean = re.sub(r'&[a-z]+;', ' ', desc_clean)  # Remove &nbsp; etc
                desc_clean = re.sub(r'class=\w+', '', desc_clean)  # Remove class= attributes
                desc_clean = re.sub(r'href=[\"\'][^\"\']+[\"\']', '', desc_clean)  # Remove href attributes
                desc_clean = re.sub(r'[^a-zA-Z0-9\s\.\,\-\:\/]', ' ', desc_clean)  # Keep only safe chars
                desc_clean = re.sub(r'\s+', ' ', desc_clean).strip()
                
                # Check if we have meaningful text
                if len(desc_clean) < 10 or desc_clean.lower().replace(match.lower(), '').strip() == '':
                    desc = f"{category}: {match}" if category else f"Important date: {match}"
                else:
                    # Use the cleaned description, but ensure it makes sense
                    if match.lower() not in desc_clean.lower()[:50]:  # Date should be near start
                        desc = f"{desc_clean[:150]} - {match}"
                    else:
                        desc = desc_clean[:200]
                
                deadlines.append({
                    'date': deadline_date.isoformat(),
                    'description': desc,
                    'category': self.categorize_deadline(category) if category else 'general',
                    'date_text': match,
                    'url': self.IMPORTANT_DATES_URL,
                    'scraped_at': datetime.utcnow().isoformat()
                })
        
        return deadlines
    
    def categorize_deadline(self, description: str) -> str:
        """Categorize a deadline based on its description."""
        description_lower = description.lower()
        
        if any(word in description_lower for word in ['payment', 'tuition', 'fee', 'pay', 'bill']):
            return 'payment'
        elif any(word in description_lower for word in ['registration', 'register', 'enrollment', 'enroll']):
            return 'registration'
        elif any(word in description_lower for word in ['drop', 'withdraw', 'withdrawal']):
            return 'withdrawal'
        elif any(word in description_lower for word in ['financial aid', 'fafsa', 'scholarship', 'grant']):
            return 'financial_aid'
        elif any(word in description_lower for word in ['class', 'course', 'semester', 'term', 'start']):
            return 'academic'
        elif any(word in description_lower for word in ['graduation', 'commencement', 'diploma']):
            return 'graduation'
        elif any(word in description_lower for word in ['holiday', 'break', 'closed']):
            return 'holiday'
        else:
            return 'general'
    
    def get_upcoming_deadlines(self, days_ahead: int = 30) -> List[Dict]:
        """
        Get deadlines within the next N days.
        
        Args:
            days_ahead: Number of days to look ahead
            
        Returns:
            List of upcoming deadlines
        """
        all_deadlines = self.extract_deadlines()
        today = datetime.now()
        cutoff = today.replace(hour=23, minute=59, second=59) + timedelta(days=days_ahead)
        
        upcoming = []
        for deadline in all_deadlines:
            try:
                deadline_date = datetime.fromisoformat(deadline['date'].replace('Z', '+00:00'))
                if today <= deadline_date <= cutoff:
                    # Calculate days until deadline
                    days_until = (deadline_date - today).days
                    deadline['days_until'] = days_until
                    upcoming.append(deadline)
            except:
                continue
        
        # Sort by date
        upcoming.sort(key=lambda x: x.get('date', ''))
        return upcoming


def main():
    """Main function to test deadline scraper."""
    scraper = DeadlineScraper()
    deadlines = scraper.extract_deadlines()
    
    print(f"\nFound {len(deadlines)} deadlines:")
    for deadline in deadlines[:10]:  # Show first 10
        print(f"  {deadline['date_text']}: {deadline['description'][:60]}... ({deadline['category']})")
    
    upcoming = scraper.get_upcoming_deadlines(days_ahead=30)
    print(f"\nUpcoming deadlines (next 30 days): {len(upcoming)}")
    for deadline in upcoming[:5]:
        print(f"  {deadline['days_until']} days: {deadline['description'][:60]}...")
    
    return deadlines


if __name__ == "__main__":
    main()

