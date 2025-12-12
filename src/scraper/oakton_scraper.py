"""
Web scraper for Oakton Community College website pages.
Collects content for building the knowledge base.
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import re
from urllib.parse import urljoin, urlparse
import time


class OaktonScraper:
    """Scrapes Oakton Community College website pages."""
    
    BASE_URL = "https://www.oakton.edu"
    
    # Pages to scrape based on requirements
    TARGET_PAGES = [
        "https://www.oakton.edu/paying-for-college/payment-options.php",
        "https://www.oakton.edu/paying-for-college/tuition-and-fees.php",
        "https://www.oakton.edu/paying-for-college/financial-aid/index.php",  # Fixed URL
        # "https://my.oakton.edu/",  # Requires login, skip for now
        "https://www.oakton.edu/admissions/register-for-classes.php",
        "https://www.oakton.edu/academics/important-dates.php",
        "https://www.oakton.edu/admissions/withdrawal-from-classes.php",
        "https://catalog.oakton.edu/academic-student-policies/payment-policy/",
        "https://catalog.oakton.edu/academic-student-policies/student-financial-assistance/",
        # "https://www.oakton.edu/student-services/advising-services.php",  # Page doesn't exist
    ]
    
    def __init__(self, delay: float = 1.0):
        """
        Initialize scraper.
        
        Args:
            delay: Delay between requests in seconds (be respectful)
        """
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep punctuation
        text = text.strip()
        return text
    
    def extract_text_from_element(self, element) -> str:
        """Extract clean text from a BeautifulSoup element."""
        if element is None:
            return ""
        
        # Create a copy to avoid modifying the original
        element_copy = element.__copy__()
        
        # Remove unwanted elements
        for tag in element_copy(["script", "style", "nav", "footer", "header", "noscript"]):
            tag.decompose()
        
        # Remove navigation and utility menus
        for nav in element_copy.find_all(class_=re.compile("nav|menu|utility|breadcrumbs", re.I)):
            nav.decompose()
        
        # Remove left navigation
        for leftnav in element_copy.find_all(class_=re.compile("leftnav|leftCol", re.I)):
            leftnav.decompose()
        
        # Remove social media and footer content
        for footer in element_copy.find_all(id=re.compile("footer|skipToFooter", re.I)):
            footer.decompose()
        
        # Remove widgets (like translate, social bars)
        for widget in element_copy.find_all(class_=re.compile("widget|socialbar|translate", re.I)):
            widget.decompose()
        
        # Remove localist/calendar widgets (they load dynamically)
        for widget in element_copy.find_all(id=re.compile("localist", re.I)):
            widget.decompose()
        
        text = element_copy.get_text(separator=' ', strip=True)
        return self.clean_text(text)
    
    def scrape_page(self, url: str) -> Optional[Dict]:
        """
        Scrape a single page.
        
        Args:
            url: URL to scrape
            
        Returns:
            Dictionary with page content, metadata, and links, or None if error
        """
        try:
            print(f"Scraping: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Extract title
            title = ""
            title_tag = soup.find('title')
            if title_tag:
                title = self.clean_text(title_tag.get_text())
            
            # Extract h1 - look for captionText first (Oakton's hero headings)
            h1 = ""
            h1_tag = soup.find(class_='captionText')
            if not h1_tag:
                h1_tag = soup.find('h1')
            if h1_tag:
                h1 = self.clean_text(h1_tag.get_text())
            
            # Find main content area - Oakton uses specific structure
            main_content_parts = []
            
            # Method 1: Find div with id="skipToContent" (main content area)
            main_content_area = soup.find(id='skipToContent')
            
            # Method 2: Find div with class containing "content col9" (main content column)
            if not main_content_area:
                main_content_area = soup.find('div', class_=re.compile(r'content.*col9', re.I))
            
            # Method 3: Find all sections with oakton-section IDs or wysiwygContent class
            if not main_content_area:
                # Collect all content sections
                content_sections = (
                    soup.find_all('section', id=re.compile(r'oakton-section', re.I)) or
                    soup.find_all(class_=re.compile(r'wysiwygContent|columnStandard', re.I)) or
                    soup.find_all('div', class_='content', limit=20)
                )
                
                if content_sections:
                    # Create a wrapper to hold all sections
                    from bs4 import BeautifulSoup as BS
                    main_content_area = BS('<div></div>', 'lxml').find('div')
                    for section in content_sections[:20]:  # Limit to prevent too much
                        main_content_area.append(section)
            
            # Method 4: Fallback - find body but remove navigation
            if not main_content_area:
                main_content_area = soup.find('body')
                if main_content_area:
                    # Remove header and navigation
                    for tag in main_content_area.find_all(['header', 'nav', 'footer']):
                        tag.decompose()
            
            # Extract content from all relevant sections
            if main_content_area:
                # Find all content sections within main area
                content_sections = (
                    main_content_area.find_all('section', class_=re.compile(r'wysiwygContent|columnStandard|accordion', re.I)) or
                    main_content_area.find_all('div', class_=re.compile(r'wysiwygContent|content', re.I)) or
                    main_content_area.find_all(id=re.compile(r'oakton-section', re.I))
                )
                
                # Also include accordion content (even if hidden by default)
                accordion_rows = main_content_area.find_all(class_=re.compile(r'accRow|accordionWrap', re.I))
                
                # Collect text from all sections
                content_texts = []
                
                # Extract from regular content sections
                for section in content_sections:
                    section_text = self.extract_text_from_element(section)
                    if section_text and len(section_text) > 50:  # Only include substantial content
                        content_texts.append(section_text)
                
                # Extract from accordion rows (includes hidden content)
                for row in accordion_rows:
                    row_text = self.extract_text_from_element(row)
                    if row_text and len(row_text) > 50:
                        content_texts.append(row_text)
                
                # If no sections found, extract from main area directly
                if not content_texts:
                    main_text = self.extract_text_from_element(main_content_area)
                    if main_text and len(main_text) > 50:
                        content_texts.append(main_text)
                
                # Join all content
                content = "\n\n".join(content_texts)
            else:
                # Last resort: extract from body
                body = soup.find('body')
                if body:
                    content = self.extract_text_from_element(body)
                else:
                    content = ""
            
            # Extract links
            links = []
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                link_text = self.clean_text(link.get_text())
                
                # Resolve relative URLs
                absolute_url = urljoin(url, href)
                
                # Only include relevant links (same domain or important external)
                if link_text and (self.BASE_URL in absolute_url or href.startswith('mailto:') or absolute_url.startswith('https://my.oakton.edu')):
                    links.append({
                        'text': link_text,
                        'url': absolute_url
                    })
            
            # Extract headings for structure
            headings = []
            for level in range(1, 7):
                for heading in soup.find_all(f'h{level}'):
                    heading_text = self.clean_text(heading.get_text())
                    if heading_text:
                        headings.append({
                            'level': level,
                            'text': heading_text
                        })
            
            result = {
                'url': url,
                'title': title,
                'h1': h1,
                'content': content,
                'headings': headings,
                'links': links,
                'scraped_at': time.time()
            }
            
            return result
            
        except requests.RequestException as e:
            print(f"Error scraping {url}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error scraping {url}: {e}")
            return None
    
    def scrape_all(self) -> List[Dict]:
        """
        Scrape all target pages.
        
        Returns:
            List of scraped page data
        """
        results = []
        
        for url in self.TARGET_PAGES:
            page_data = self.scrape_page(url)
            if page_data:
                results.append(page_data)
            
            # Be respectful with delays
            time.sleep(self.delay)
        
        return results
    
    def get_category_from_url(self, url: str) -> str:
        """Determine category based on URL."""
        if 'payment' in url.lower() or 'tuition' in url.lower() or 'fee' in url.lower():
            return 'payment'
        elif 'financial-aid' in url.lower() or 'assistance' in url.lower():
            return 'financial_aid'
        elif 'register' in url.lower():
            return 'registration'
        elif 'withdrawal' in url.lower() or 'drop' in url.lower():
            return 'withdrawal'
        elif 'important-dates' in url.lower() or 'deadline' in url.lower():
            return 'deadlines'
        elif 'advising' in url.lower() or 'advisor' in url.lower():
            return 'advising'
        elif 'portal' in url.lower() or 'my.oakton' in url.lower():
            return 'portal'
        elif 'policy' in url.lower():
            return 'policies'
        else:
            return 'general'


def main():
    """Main function to run scraper."""
    scraper = OaktonScraper()
    results = scraper.scrape_all()
    
    print(f"\nScraped {len(results)} pages successfully")
    
    # Print summary
    for result in results:
        category = scraper.get_category_from_url(result['url'])
        print(f"  - {category}: {result['url']} ({len(result['content'])} chars)")
    
    return results


if __name__ == "__main__":
    main()

