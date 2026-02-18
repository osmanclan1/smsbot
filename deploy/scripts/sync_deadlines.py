#!/usr/bin/env python3
"""
Script to sync deadlines from Oakton website to DynamoDB.
Run periodically (e.g., daily) to keep deadlines up to date.
"""

import sys
import os

# Add src directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from scraper.deadline_scraper import DeadlineScraper
from storage.dynamodb import DynamoDBService


def sync_deadlines():
    """Sync deadlines from website to DynamoDB."""
    print("Starting deadline sync...")
    
    scraper = DeadlineScraper()
    db = DynamoDBService()
    
    if not db.deadlines_table:
        print("ERROR: Deadlines table does not exist. Please create it first.")
        return False
    
    # Scrape deadlines
    print("Scraping deadlines from Oakton website...")
    deadlines = scraper.extract_deadlines()
    
    if not deadlines:
        print("WARNING: No deadlines found. Check scraper logic.")
        return False
    
    print(f"Found {len(deadlines)} deadlines")
    
    # Store each deadline
    stored_count = 0
    for deadline in deadlines:
        try:
            db.store_deadline(deadline)
            stored_count += 1
        except Exception as e:
            print(f"Error storing deadline '{deadline.get('description', 'unknown')}': {e}")
    
    print(f"Successfully stored {stored_count} deadlines")
    
    # Show upcoming deadlines
    upcoming = db.get_upcoming_deadlines(days_ahead=30)
    print(f"\nUpcoming deadlines (next 30 days): {len(upcoming)}")
    for deadline in upcoming[:5]:
        print(f"  {deadline.get('days_until', '?')} days: {deadline.get('description', '')[:60]}...")
    
    return True


if __name__ == "__main__":
    success = sync_deadlines()
    sys.exit(0 if success else 1)

