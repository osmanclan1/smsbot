"""
Content processor for preparing scraped content for Pinecone.
Chunks text, generates embeddings, and uploads to Pinecone vector database.
"""

import os
import tiktoken
from typing import List, Dict, Optional

# Patch httpx before importing OpenAI/Pinecone to fix proxy compatibility issue
import httpx
original_client_init = httpx.Client.__init__
original_async_init = httpx.AsyncClient.__init__

def patched_client_init(self, *args, **kwargs):
    """Patch to remove proxies parameter that causes issues with newer httpx."""
    kwargs.pop('proxies', None)
    return original_client_init(self, *args, **kwargs)

def patched_async_init(self, *args, **kwargs):
    """Patch to remove proxies parameter that causes issues with newer httpx."""
    kwargs.pop('proxies', None)
    return original_async_init(self, *args, **kwargs)

# Apply patches
httpx.Client.__init__ = patched_client_init
httpx.AsyncClient.__init__ = patched_async_init

from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec
import time


class ContentProcessor:
    """Processes scraped content for Pinecone vector database."""
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        pinecone_api_key: Optional[str] = None,
        pinecone_index_name: str = "oakton-knowledge-base",
        pinecone_environment: str = "us-east1-gcp"
    ):
        """
        Initialize content processor.
        
        Args:
            openai_api_key: OpenAI API key (or from env)
            pinecone_api_key: Pinecone API key (or from env)
            pinecone_index_name: Name of Pinecone index
            pinecone_environment: Pinecone environment/region
        """
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.pinecone_api_key = pinecone_api_key or os.getenv("PINECONE_API_KEY")
        self.pinecone_index_name = pinecone_index_name or os.getenv("PINECONE_INDEX_NAME", "oakton-knowledge-base")
        
        if not self.openai_api_key:
            raise ValueError("OpenAI API key required")
        if not self.pinecone_api_key:
            raise ValueError("Pinecone API key required")
        
        self.openai_client = OpenAI(api_key=self.openai_api_key)
        self.pinecone_client = Pinecone(api_key=self.pinecone_api_key)
        
        # Initialize encoding for token counting
        self.encoding = tiktoken.encoding_for_model("text-embedding-ada-002")
        
        # Ensure index exists
        self._ensure_index()
    
    def _ensure_index(self):
        """Ensure Pinecone index exists, create if not."""
        existing_indexes = [index.name for index in self.pinecone_client.list_indexes()]
        
        if self.pinecone_index_name not in existing_indexes:
            print(f"Creating Pinecone index: {self.pinecone_index_name}")
            self.pinecone_client.create_index(
                name=self.pinecone_index_name,
                dimension=1536,  # OpenAI ada-002 embedding dimension
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
            # Wait for index to be ready
            time.sleep(5)
        else:
            print(f"Using existing Pinecone index: {self.pinecone_index_name}")
        
        self.index = self.pinecone_client.Index(self.pinecone_index_name)
    
    def chunk_text(
        self,
        text: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        max_chunk_size: int = 8000
    ) -> List[str]:
        """
        Chunk text into smaller pieces for embedding.
        
        Args:
            text: Text to chunk
            chunk_size: Target chunk size in tokens
            chunk_overlap: Overlap between chunks in tokens
            max_chunk_size: Maximum chunk size (to prevent oversized chunks)
            
        Returns:
            List of text chunks
        """
        if not text or len(text.strip()) == 0:
            return []
        
        # Tokenize text
        tokens = self.encoding.encode(text)
        
        if len(tokens) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(tokens):
            # Calculate end position
            end = min(start + chunk_size, len(tokens))
            
            # Try to break at sentence boundaries
            chunk_tokens = tokens[start:end]
            
            # Decode chunk
            chunk_text = self.encoding.decode(chunk_tokens)
            
            # If not the last chunk, try to break at sentence end
            if end < len(tokens) and len(chunk_tokens) > chunk_size * 0.7:
                # Look for sentence endings in last 20% of chunk
                search_start = int(len(chunk_tokens) * 0.8)
                for i in range(len(chunk_tokens) - 1, search_start, -1):
                    char = self.encoding.decode([chunk_tokens[i]])
                    if char in ['.', '!', '?', '\n']:
                        chunk_tokens = chunk_tokens[:i+1]
                        chunk_text = self.encoding.decode(chunk_tokens)
                        end = start + len(chunk_tokens)
                        break
            
            chunks.append(chunk_text.strip())
            
            # Move start with overlap
            start = end - chunk_overlap if end < len(tokens) else end
        
        return chunks
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using OpenAI.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        response = self.openai_client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        return response.data[0].embedding
    
    def process_page(self, page_data: Dict, category: Optional[str] = None) -> int:
        """
        Process a single scraped page: chunk, embed, upload to Pinecone.
        
        Args:
            page_data: Scraped page data from scraper
            category: Optional category override
            
        Returns:
            Number of chunks uploaded
        """
        url = page_data['url']
        title = page_data.get('title', '')
        h1 = page_data.get('h1', '')
        content = page_data.get('content', '')
        headings = page_data.get('headings', [])
        links = page_data.get('links', [])
        
        if not content:
            print(f"Skipping {url}: no content")
            return 0
        
        # Determine category
        if not category:
            from .oakton_scraper import OaktonScraper
            category = OaktonScraper().get_category_from_url(url)
        
        # Create full text with metadata context
        full_text_parts = []
        if title:
            full_text_parts.append(f"Title: {title}")
        if h1 and h1 != title:
            full_text_parts.append(f"Main Heading: {h1}")
        
        # Add headings structure
        if headings:
            heading_text = " | ".join([h['text'] for h in headings[:5]])
            full_text_parts.append(f"Section Headings: {heading_text}")
        
        full_text_parts.append(content)
        
        full_text = "\n\n".join(full_text_parts)
        
        # Chunk the content
        chunks = self.chunk_text(full_text)
        
        if not chunks:
            print(f"No chunks generated for {url}")
            return 0
        
        print(f"Processing {url}: {len(chunks)} chunks")
        
        # Generate embeddings and prepare vectors
        vectors_to_upsert = []
        
        for i, chunk in enumerate(chunks):
            try:
                embedding = self.generate_embedding(chunk)
                
                # Create unique ID
                vector_id = f"{url.replace('https://', '').replace('http://', '').replace('/', '_')}_{i}"
                
                # Prepare metadata
                metadata = {
                    'url': url,
                    'title': title,
                    'h1': h1,
                    'category': category,
                    'chunk_index': i,
                    'total_chunks': len(chunks),
                    'text': chunk[:1000]  # Store first 1000 chars for reference
                }
                
                # Add important links
                if links:
                    important_links = [
                        f"{link['text']}: {link['url']}" 
                        for link in links[:5]
                    ]
                    metadata['links'] = " | ".join(important_links)
                
                vectors_to_upsert.append({
                    'id': vector_id,
                    'values': embedding,
                    'metadata': metadata
                })
                
                # Small delay to respect rate limits
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error processing chunk {i} of {url}: {e}")
                continue
        
        # Upload to Pinecone in batches
        if vectors_to_upsert:
            batch_size = 100
            for i in range(0, len(vectors_to_upsert), batch_size):
                batch = vectors_to_upsert[i:i+batch_size]
                try:
                    self.index.upsert(vectors=batch)
                    print(f"Uploaded batch {i//batch_size + 1} ({len(batch)} vectors)")
                except Exception as e:
                    print(f"Error uploading batch: {e}")
        
        return len(vectors_to_upsert)
    
    def process_all_pages(self, pages_data: List[Dict]) -> Dict[str, int]:
        """
        Process all scraped pages.
        
        Args:
            pages_data: List of scraped page data
            
        Returns:
            Dictionary with processing statistics
        """
        stats = {
            'total_pages': len(pages_data),
            'total_chunks': 0,
            'processed_pages': 0
        }
        
        for page_data in pages_data:
            try:
                chunks_count = self.process_page(page_data)
                stats['total_chunks'] += chunks_count
                if chunks_count > 0:
                    stats['processed_pages'] += 1
            except Exception as e:
                print(f"Error processing page {page_data.get('url', 'unknown')}: {e}")
        
        return stats


def main():
    """Main function to run content processor."""
    from .oakton_scraper import OaktonScraper
    
    # Scrape pages
    print("Scraping Oakton pages...")
    scraper = OaktonScraper()
    pages_data = scraper.scrape_all()
    
    # Process and upload to Pinecone
    print("\nProcessing content and uploading to Pinecone...")
    processor = ContentProcessor()
    stats = processor.process_all_pages(pages_data)
    
    print(f"\nProcessing complete!")
    print(f"  Pages processed: {stats['processed_pages']}/{stats['total_pages']}")
    print(f"  Total chunks uploaded: {stats['total_chunks']}")


if __name__ == "__main__":
    main()

