#!/usr/bin/env python3
"""
Script to scrape Oakton website and populate Pinecone knowledge base.
Run this before deploying to populate the knowledge base.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from src.scraper.oakton_scraper import OaktonScraper
from src.scraper.content_processor import ContentProcessor


def main():
    """Main function."""
    print("=" * 60)
    print("Oakton Website Scraper & Knowledge Base Builder")
    print("=" * 60)
    
    # Step 1: Scrape pages
    print("\n[1/2] Scraping Oakton website pages...")
    scraper = OaktonScraper()
    pages_data = scraper.scrape_all()
    
    if not pages_data:
        print("ERROR: No pages scraped. Exiting.")
        return 1
    
    print(f"✓ Scraped {len(pages_data)} pages")
    
    # Step 2: Process and upload to Pinecone
    print("\n[2/2] Processing content and uploading to Pinecone...")
    processor = ContentProcessor()
    stats = processor.process_all_pages(pages_data)
    
    print("\n" + "=" * 60)
    print("Processing Complete!")
    print("=" * 60)
    print(f"Pages processed: {stats['processed_pages']}/{stats['total_pages']}")
    print(f"Total chunks uploaded: {stats['total_chunks']}")
    print("\nKnowledge base is ready for use!")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

