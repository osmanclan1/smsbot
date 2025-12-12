"""
Knowledge base service for querying Pinecone vector database.
"""

import os
import tiktoken
from typing import List, Dict, Optional
from openai import OpenAI

# Patch httpx before importing Pinecone to fix proxy compatibility issue
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

from pinecone import Pinecone


class KnowledgeBaseService:
    """Service for querying Pinecone knowledge base."""
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        pinecone_api_key: Optional[str] = None,
        pinecone_index_name: Optional[str] = None
    ):
        """Initialize knowledge base service."""
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.pinecone_api_key = pinecone_api_key or os.getenv("PINECONE_API_KEY")
        self.pinecone_index_name = pinecone_index_name or os.getenv("PINECONE_INDEX_NAME", "oakton-knowledge-base")
        
        if not self.openai_api_key:
            raise ValueError("OpenAI API key required")
        if not self.pinecone_api_key:
            raise ValueError("Pinecone API key required")
        
        # Initialize OpenAI client
        self.openai_client = OpenAI(api_key=self.openai_api_key)
        
        # Initialize Pinecone client (httpx is already patched at module level)
        self.pinecone_client = Pinecone(api_key=self.pinecone_api_key)
        self.index = self.pinecone_client.Index(self.pinecone_index_name)
        
        # Initialize tiktoken for token counting
        self.encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for query text."""
        response = self.openai_client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        return response.data[0].embedding
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        filter_dict: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Search knowledge base for relevant context.
        
        Args:
            query: Search query text
            top_k: Number of results to return
            filter_dict: Optional metadata filter
            
        Returns:
            List of relevant contexts with metadata
        """
        # Generate embedding for query
        query_embedding = self.generate_embedding(query)
        
        # Search Pinecone
        search_kwargs = {
            'vector': query_embedding,
            'top_k': top_k,
            'include_metadata': True
        }
        
        if filter_dict:
            search_kwargs['filter'] = filter_dict
        
        results = self.index.query(**search_kwargs)
        
        # Format results
        contexts = []
        for match in results.matches:
            metadata = match.metadata or {}
            contexts.append({
                'score': match.score,
                'text': metadata.get('text', ''),
                'url': metadata.get('url', ''),
                'title': metadata.get('title', ''),
                'category': metadata.get('category', ''),
                'links': metadata.get('links', '')
            })
        
        return contexts
    
    def get_context_for_conversation(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict]] = None,
        top_k: int = 3,
        prioritize_links: bool = False
    ) -> str:
        """
        Get relevant context for a conversation message.
        
        Args:
            user_message: Current user message
            conversation_history: Previous messages in conversation
            top_k: Number of contexts to retrieve
            prioritize_links: If True, prioritize contexts with links and extract them
            
        Returns:
            Formatted context string
        """
        # Build query from current message and recent history
        query_parts = [user_message]
        
        if conversation_history:
            # Add last few messages for context
            recent_messages = conversation_history[-3:]
            for msg in recent_messages:
                if msg.get('role') == 'user':
                    query_parts.append(msg.get('content', ''))
        
        query = " ".join(query_parts)
        
        # Search knowledge base - get more results if prioritizing links
        search_top_k = top_k * 2 if prioritize_links else top_k
        contexts = self.search(query, top_k=search_top_k)
        
        if not contexts:
            return ""
        
        # If prioritizing links, filter and sort by link availability
        if prioritize_links:
            contexts_with_links = [ctx for ctx in contexts if ctx.get('url') or ctx.get('links')]
            contexts_without_links = [ctx for ctx in contexts if not (ctx.get('url') or ctx.get('links'))]
            # Prioritize contexts with links
            contexts = contexts_with_links[:top_k] + contexts_without_links[:max(1, top_k - len(contexts_with_links))]
        
        # Format contexts with truncation to limit token usage
        context_parts = []
        max_tokens_per_chunk = 500  # Limit each chunk to ~500 tokens
        
        for ctx in contexts:
            # Build context with essential info only
            parts = []
            
            # Add title if available
            if ctx.get('title'):
                parts.append(ctx['title'])
            
            # Truncate text content to max_tokens_per_chunk
            text_content = ctx.get('text', '')
            if text_content:
                tokens = self.encoding.encode(text_content)
                if len(tokens) > max_tokens_per_chunk:
                    # Truncate to max tokens and decode back
                    truncated_tokens = tokens[:max_tokens_per_chunk]
                    text_content = self.encoding.decode(truncated_tokens)
                    # Try to end at a sentence boundary
                    if text_content and not text_content[-1] in '.!?\n':
                        last_period = text_content.rfind('.')
                        last_newline = text_content.rfind('\n')
                        cut_point = max(last_period, last_newline)
                        if cut_point > max_tokens_per_chunk * 0.7:  # Only if we keep at least 70% of content
                            text_content = text_content[:cut_point + 1]
                
                parts.append(text_content)
            
            # Add URL (essential for references)
            if ctx.get('url'):
                parts.append(f"Source: {ctx['url']}")
            
            # Add extracted links if available and prioritizing links
            if prioritize_links and ctx.get('links'):
                links = ctx.get('links', [])
                if isinstance(links, list) and len(links) > 0:
                    link_texts = []
                    for link in links[:3]:  # Limit to 3 most relevant links
                        if isinstance(link, dict):
                            link_url = link.get('url', '')
                            link_text = link.get('text', '')
                            if link_url:
                                link_texts.append(f"{link_text}: {link_url}" if link_text else link_url)
                    if link_texts:
                        parts.append(f"Relevant links: {' | '.join(link_texts)}")
            
            # Join parts (removed category and links to reduce tokens)
            if parts:
                context_text = "\n".join(parts)
                context_parts.append(context_text.strip())
        
        return "\n\n---\n\n".join(context_parts)
    
    def search_for_links(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Search for links specifically. Returns contexts with URLs and extracted links.
        
        Args:
            query: Search query text
            top_k: Number of results to return
            
        Returns:
            List of contexts with link information
        """
        contexts = self.search(query, top_k=top_k * 2)  # Get more results to filter
        
        # Filter to only contexts with links
        contexts_with_links = []
        for ctx in contexts:
            if ctx.get('url') or ctx.get('links'):
                contexts_with_links.append(ctx)
            if len(contexts_with_links) >= top_k:
                break
        
        return contexts_with_links

