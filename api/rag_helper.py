"""
RAG Helper Module for Movie Chatbot
Provides vector database search and context injection for LLM
"""

from api.vector_db import get_vector_db
from datetime import datetime
from typing import Dict, List, Any, Optional
import re
import json


# Initialize vector database
try:
    vector_db = get_vector_db(persist_directory="./chroma_db")
    print(f"✓ RAG: Vector database loaded with {vector_db.count_movies()} media items")
    RAG_ENABLED = True
except Exception as e:
    print(f"⚠ RAG: Vector database not available: {e}")
    vector_db = None
    RAG_ENABLED = False


def search_tmdb_for_media(title: str, year: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Search TMDb API for a specific media title with fuzzy matching.
    
    Args:
        title: Media title to search for
        year: Optional year to filter results
    
    Returns:
        Dictionary with media info or None if not found
    """
    try:
        import requests
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        TMDB_API_KEY = os.getenv("TMDB_API_KEY")
        
        if not TMDB_API_KEY:
            print("  ✗ TMDb API key not found")
            return None
        
        # Try searching for TV shows first
        tv_url = f"https://api.themoviedb.org/3/search/tv"
        params = {
            "api_key": TMDB_API_KEY,
            "query": title,
            "include_adult": True
        }
        if year:
            params["first_air_date_year"] = year
        
        response = requests.get(tv_url, params=params, timeout=5)
        results = response.json().get("results", [])
        
        # If not found in TV, try movies
        if not results:
            movie_url = f"https://api.themoviedb.org/3/search/movie"
            params_movie = {
                "api_key": TMDB_API_KEY,
                "query": title,
                "include_adult": True
            }
            if year:
                params_movie["year"] = year
            
            response = requests.get(movie_url, params=params_movie, timeout=5)
            results = response.json().get("results", [])
            media_type = "movie"
        else:
            media_type = "tv"
        
        if results:
            # Get the first result
            result = results[0]
            return {
                "title": result.get("name" if media_type == "tv" else "title"),
                "year": (result.get("first_air_date" if media_type == "tv" else "release_date") or "")[:4],
                "overview": result.get("overview", ""),
                "media_type": media_type,
                "id": result.get("id")
            }
        
        return None
    except Exception as e:
        print(f"  ✗ TMDb search error: {e}")
        return None


def is_recent_movie_query(query: str) -> bool:
    """
    Detect if the query is about recent movies or TV shows (2022-2025).
    
    Args:
        query: User's message
    
    Returns:
        True if query mentions recent years or recent media indicators
    """
    current_year = datetime.now().year
    recent_years = [str(year) for year in range(2022, current_year + 2)]
    
    # Check for year mentions
    if any(year in query for year in recent_years):
        return True
    
    # Check for recent media indicators
    recent_indicators = [
        'recent', 'new', 'latest', 'upcoming', '2022', '2023', '2024', '2025',
        'this year', 'last year', 'coming out', 'just released', 'just came out',
        'came out', 'out now', 'currently', 'in theaters', 'in theatre',
        'release this year', 'released this year', 'release last year',
        'from this year', 'from last year', 'from 2024', 'from 2025',
        'tv show', 'series', 'anime', 'season', 'episode'
    ]
    
    query_lower = query.lower()
    return any(indicator in query_lower for indicator in recent_indicators)


def search_vector_db(query: str, top_k: int = 5) -> Optional[Dict[str, Any]]:
    """
    Search the vector database for relevant media.
    
    Args:
        query: Search query
        top_k: Number of results to return
    
    Returns:
        Search results or None if RAG is disabled
    """
    if not RAG_ENABLED or vector_db is None:
        return None
    
    try:
        results = vector_db.search(query, top_k=top_k)
        return results
    except Exception as e:
        print(f"Error searching vector database: {e}")
        return None


def format_vector_context(search_results: Dict[str, Any]) -> str:
    """
    Format vector database search results into context for LLM.
    
    Args:
        search_results: Results from vector database search
    
    Returns:
        Formatted context string
    """
    if not search_results or not search_results.get('ids') or not search_results['ids'][0]:
        return ""
    
    context_parts = []
    context_parts.append("**Recent Media from Database:**\n")
    
    for i, movie_id in enumerate(search_results['ids'][0]):
        metadata = search_results['metadatas'][0][i]
        similarity = 1 - search_results['distances'][0][i]
        
        title = metadata.get('title', 'Unknown')
        year = metadata.get('release_year', 'Unknown')
        genres = metadata.get('genres', 'Unknown')
        director = metadata.get('director', 'Unknown')
        cast = metadata.get('cast', 'Unknown')
        rating = metadata.get('vote_average', 0)
        media_type = metadata.get('media_type', 'movie')
        
        # Create explicit type labels
        if media_type == 'anime_tv':
            type_label = "Anime Series"
        elif media_type == 'anime_movie':
            type_label = "Anime Movie"
        elif media_type == 'tv':
            type_label = "TV Show"
        else:
            type_label = "Movie"
        
        # TV Specific details
        extra_info = ""
        if media_type in ['tv', 'anime_tv']:
            seasons = metadata.get('number_of_seasons')
            if seasons:
                extra_info = f" ({seasons} Seasons)"
        
        context_parts.append(f"\n{i+1}. **{title}** ({year}) [{type_label}{extra_info}]")
        context_parts.append(f"   - Genres: {genres}")
        if media_type in ['movie', 'anime_movie']:
            context_parts.append(f"   - Director: {director}")
        elif media_type in ['tv', 'anime_tv'] and metadata.get('created_by'):
            context_parts.append(f"   - Created By: {metadata.get('created_by')}")
            
        context_parts.append(f"   - Cast: {cast}")
        context_parts.append(f"   - Rating: {rating}/10")
        context_parts.append(f"   - Relevance: {similarity:.2%}")
    
    return "\n".join(context_parts)


def extract_media_name_from_query(query: str) -> tuple[Optional[str], Optional[str]]:
    """
    Extract the media name and year that the user is asking about from their query.
    
    Args:
        query: User's query
    
    Returns:
        Tuple of (media_name, year) or (None, None)
    """
    try:
        from api.chatbot import get_chatbot, clean_json_response
        
        # Determine the current year for "this year" queries
        current_year = datetime.now().year
        
        extraction_prompt = f"""Extract the movie/TV show name and year the user is asking about. Return ONLY valid JSON.

Current year: {current_year}

Query: {query}

Examples:
- "suggest me movie like weapon" → {{"media": "weapon", "year": null}}
- "movies similar to Inception from 2010" → {{"media": "Inception", "year": "2010"}}
- "horror films like The Conjuring released this year" → {{"media": "The Conjuring", "year": "{current_year}"}}
- "tv shows like Breaking Bad" → {{"media": "Breaking Bad", "year": null}}
- "anime similar to Attack on Titan" → {{"media": "Attack on Titan", "year": null}}

Return format:
{{"media": "name here", "year": "YYYY or null"}}"""
        
        response = get_chatbot().invoke(extraction_prompt)
        cleaned = clean_json_response(response.content)
        data = json.loads(cleaned)
        media_name = data.get("media", "").strip()
        year = data.get("year")
        
        if media_name:
            year_str = f" ({year})" if year else ""
            print(f"🎬 RAG: Extracted media: '{media_name}'{year_str}")
            return media_name, year
        return None, None
    except Exception as e:
        print(f"  ✗ Error extracting media name: {e}")
        return None, None


def enhance_prompt_with_rag(
    user_message: str, 
    chat_history: str = "",
    source_title: str = None,
    source_year: str = None
) -> tuple[str, bool, list]:
    """
    Enhance the user's prompt with RAG context.
    
    NEW: LLM-first approach - LLM provides source_title and source_year.
    
    Args:
        user_message: User's original message
        chat_history: Previous chat history (optional)
        source_title: Source media title (provided by LLM analysis)
        source_year: Source media year (provided by LLM analysis)
    
    Returns:
        Tuple of (enhanced_prompt, rag_used, media_ids)
    """
    if not RAG_ENABLED:
        return user_message, False, []
    
    search_results = None
    
    # If LLM provided source title, use hybrid search
    if source_title:
        print(f"  → Step 1: Exact title search for: '{source_title}' ({source_year or 'any year'})")
        
        # Try exact match first
        exact_match = vector_db.search_by_exact_title(source_title, source_year)
        
        if exact_match:
            print(f"  ✓ Exact match found!")
            
            # Use the exact match's description to find similar items
            search_results = search_vector_db(exact_match['document'], top_k=6)
            
        else:
            print(f"  ✗ No exact match found")
            print(f"  → Step 2: Trying semantic search...")
            
            # Fallback to semantic search
            search_query = f"{source_title} {source_year or ''}"
            search_results = search_vector_db(search_query, top_k=5)
            
            # Validate semantic search results
            if search_results and search_results.get('ids') and search_results['ids'][0]:
                first_result_title = search_results['metadatas'][0][0].get('title', '').lower()
                source_title_lower = source_title.lower()
                
                # Check if first result is actually relevant
                if source_title_lower not in first_result_title and first_result_title not in source_title_lower:
                    print(f"  ✗ Semantic search returned irrelevant: '{search_results['metadatas'][0][0].get('title')}'")
                    print(f"  → Step 3: Trying TMDb fallback...")
                    
                    # Try TMDb fallback
                    tmdb_result = search_tmdb_for_media(source_title, source_year)
                    if tmdb_result:
                        print(f"  ✓ Found on TMDb: {tmdb_result['title']}")
                        search_query = f"{tmdb_result['title']} {tmdb_result.get('overview', '')[:200]}"
                        search_results = search_vector_db(search_query, top_k=5)
                    else:
                        print(f"  ✗ Not found on TMDb either")
                        return user_message, False, []
    else:
        # No source title, do general search
        search_results = search_vector_db(user_message, top_k=5)
    
    if not search_results or not search_results.get('ids') or not search_results['ids'][0]:
        return user_message, False, []
    
    # Extract media IDs from search results
    media_ids = [int(media_id) for media_id in search_results['ids'][0]]
    
    # Format context
    context = format_vector_context(search_results)
    
    # Create enhanced prompt with clearer instructions
    enhanced_prompt = f"""You are a media recommendation assistant with access to an up-to-date database of movies and TV shows.

{context}

**User Query:** {user_message}

**Instructions:**
- The database above contains recent movies and TV shows (2022-2025)
- Each item is labeled as [Movie] or [TV Show] - PAY ATTENTION to this distinction
- The FIRST item listed is likely the source media the user is asking about
- The OTHER items are semantically similar based on themes, genres, and style
- **IMPORTANT**: If the source is a TV SHOW, prioritize recommending other TV SHOWS from the list
- **IMPORTANT**: If the source is a MOVIE, prioritize recommending other MOVIES from the list
- You can also recommend additional movies/shows from your general knowledge
- Explain WHY each recommendation is similar (matching genres, themes, tone, creator style, etc.)
- Focus on thematic similarity: if source is horror/mystery, recommend other horror/mystery content
- Be conversational and helpful
- **ALWAYS mention whether each recommendation is a Movie or TV Show**

**Example:**
User asks: "suggest me tv show like Breaking Bad"
- Source: Breaking Bad [TV Show] (crime drama, anti-hero)
- Similar from DB: Better Call Saul [TV Show], Ozark [TV Show] (crime, moral ambiguity)
- Additional: The Sopranos [TV Show] (similar themes)

Please provide thoughtful recommendations based on the SOURCE media's themes, genres, and style. Remember to specify if each recommendation is a Movie or TV Show."""
    
    return enhanced_prompt, True, media_ids


def get_rag_stats() -> Dict[str, Any]:
    """
    Get RAG system statistics.
    
    Returns:
        Dictionary with RAG stats
    """
    if not RAG_ENABLED or vector_db is None:
        return {
            'enabled': False,
            'total_movies': 0,
            'status': 'disabled'
        }
    
    try:
        total_movies = vector_db.count_movies()
        return {
            'enabled': True,
            'total_movies': total_movies,
            'status': 'active'
        }
    except Exception as e:
        return {
            'enabled': False,
            'total_movies': 0,
            'status': f'error: {str(e)}'
        }
