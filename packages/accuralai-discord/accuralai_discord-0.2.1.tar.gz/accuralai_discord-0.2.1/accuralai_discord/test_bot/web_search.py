"""Web search functionality using Google's grounding with Google Search."""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

LOGGER = logging.getLogger("accuralai.discord.test")

# Try to import Google GenAI SDK for Google Search grounding
try:
    from google import genai
    from google.genai import types as genai_types
    GOOGLE_GENAI_AVAILABLE = True
except ImportError:
    genai = None
    genai_types = None
    GOOGLE_GENAI_AVAILABLE = False

# Try to import config loader for reading AccuralAI config
try:
    from accuralai_core.config.loader import load_from_file
    CONFIG_LOADER_AVAILABLE = True
except ImportError:
    load_from_file = None
    CONFIG_LOADER_AVAILABLE = False


def _get_api_key_from_config(config_path: Optional[str] = None) -> Optional[str]:
    """
    Get Google GenAI API key from AccuralAI config file.
    
    Args:
        config_path: Path to config.toml file. If None, tries to load from
                    ACCURALAI_CONFIG_PATH environment variable.
        
    Returns:
        API key if found, None otherwise
    """
    if not CONFIG_LOADER_AVAILABLE:
        return None
    
    try:
        # Try config_path parameter first
        if config_path and os.path.exists(config_path):
            config_data = load_from_file(config_path)
            api_key = config_data.get("backends", {}).get("google", {}).get("options", {}).get("api_key")
            if api_key:
                LOGGER.debug(f"Loaded API key from config: {config_path}")
                return api_key
        
        # Try environment variable for config path
        env_config_path = os.getenv("ACCURALAI_CONFIG_PATH")
        if env_config_path:
            env_config_path = os.path.expanduser(env_config_path)
            if not os.path.isabs(env_config_path):
                env_config_path = os.path.abspath(env_config_path)
            if os.path.exists(env_config_path):
                config_data = load_from_file(env_config_path)
                api_key = config_data.get("backends", {}).get("google", {}).get("options", {}).get("api_key")
                if api_key:
                    LOGGER.debug(f"Loaded API key from config: {env_config_path}")
                    return api_key
        
        # Try default config.toml in current directory
        default_config = os.path.abspath("config.toml")
        if os.path.exists(default_config):
            config_data = load_from_file(default_config)
            api_key = config_data.get("backends", {}).get("google", {}).get("options", {}).get("api_key")
            if api_key:
                LOGGER.debug(f"Loaded API key from default config.toml")
                return api_key
                
    except Exception as e:
        LOGGER.debug(f"Failed to load API key from config: {e}")
    
    return None


async def search_web(
    query: str, 
    max_results: int = 5,
    config_path: Optional[str] = None,
    api_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Perform a web search using Google's grounding with Google Search.
    
    This uses Google's built-in grounding feature which connects the Gemini model
    to real-time web content via Google Search. See:
    https://ai.google.dev/gemini-api/docs/google-search
    
    The API key is loaded from (in order):
    1. The api_key parameter (if provided)
    2. The AccuralAI config file at config_path (or ACCURALAI_CONFIG_PATH env var)
    3. The GOOGLE_GENAI_API_KEY environment variable
    
    Args:
        query: Search query
        max_results: Maximum number of results to return
        config_path: Optional path to AccuralAI config.toml file
        api_key: Optional API key (overrides config and env var)
        
    Returns:
        List of search results with title, url, and snippet
    """
    if not query or len(query.strip()) < 3:
        return [{"error": "Search query must be at least 3 characters"}]
    
    if not GOOGLE_GENAI_AVAILABLE:
        return [{"error": "Google GenAI SDK is not available. Please install it with: pip install google-genai"}]
    
    # Get API key from parameter, config file, or environment variable (in that order)
    if not api_key:
        api_key = _get_api_key_from_config(config_path)
    
    if not api_key:
        api_key = os.getenv("GOOGLE_GENAI_API_KEY")
    
    if not api_key:
        return [{"error": "Google GenAI API key not found. Please set it in config.toml ([backends.google.options.api_key]) or GOOGLE_GENAI_API_KEY environment variable."}]
    
    try:
        # Wrap synchronous call in async executor since Google GenAI SDK is synchronous
        def _do_search():
            # Create client
            client = genai.Client(api_key=api_key)
            
            # Use Google's grounding with Google Search
            # For newer models (2.0+), use google_search tool
            model = os.getenv("GOOGLE_SEARCH_MODEL", "gemini-2.5-flash-lite")
            
            # Create the grounding tool using proper types
            grounding_tool = genai_types.Tool(
                google_search=genai_types.GoogleSearch()
            )
            
            config = genai_types.GenerateContentConfig(
                tools=[grounding_tool]
            )
            
            # The model will automatically use Google Search to ground the query
            response = client.models.generate_content(
                model=model,
                contents=query,
                config=config,
            )
            
            # Extract search results from grounding metadata
            results = []
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                    metadata = candidate.grounding_metadata
                    
                    # Extract grounding chunks (search results)
                    if hasattr(metadata, 'grounding_chunks') and metadata.grounding_chunks:
                        for chunk in metadata.grounding_chunks[:max_results]:
                            # Check if chunk has web search data
                            if hasattr(chunk, 'web') and chunk.web:
                                web = chunk.web
                                title = getattr(web, 'title', 'Untitled') or 'Untitled'
                                uri = getattr(web, 'uri', '#') or '#'
                                # Try to get snippet from web, otherwise use title
                                snippet = getattr(web, 'snippet', None) or getattr(web, 'title', '') or ''
                                
                                results.append({
                                    "title": title[:200],
                                    "url": uri,
                                    "snippet": snippet[:300],
                                })
            
            return results if results else []
        
        # Run synchronous Google GenAI call in thread pool
        results = await asyncio.to_thread(_do_search)
        
        if results:
            LOGGER.debug(f"Google Search returned {len(results)} results")
            return results
        else:
            LOGGER.debug("Google Search returned no results")
            return [{"error": "No search results found"}]
            
    except Exception as e:
        LOGGER.exception(f"Google Search error: {e}")
        return [{"error": f"Search failed: {str(e)}"}]


def format_search_results(results: List[Dict[str, Any]]) -> str:
    """
    Format search results for Discord message.
    
    Args:
        results: List of search results
        
    Returns:
        Formatted string
    """
    if not results:
        return "No search results found."
    
    if results[0].get("error"):
        return f"❌ {results[0]['error']}"
    
    lines = ["**Search Results:**\n"]
    for i, result in enumerate(results, 1):
        title = result.get("title", "Untitled")
        url = result.get("url", "#")
        snippet = result.get("snippet", "")
        note = result.get("note")
        
        lines.append(f"{i}. **{title}**")
        lines.append(f"   {url}")
        if snippet and snippet != title:
            lines.append(f"   {snippet[:200]}")
            if len(snippet) > 200:
                lines[-1] += "..."
        if note:
            lines.append(f"   ⚠️ {note}")
        lines.append("")
    
    return "\n".join(lines)

