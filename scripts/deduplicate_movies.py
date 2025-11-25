"""
Prevent Duplicate Movies Utility

This script checks for duplicate movies and updates upcoming movies
that have been released with full information.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any


def load_existing_movies(filepath: str = "data/movies.json") -> Dict[int, Dict]:
    """
    Load existing movies indexed by TMDb ID.
    
    Returns:
        Dictionary mapping movie_id to movie data
    """
    if not os.path.exists(filepath):
        return {}
    
    with open(filepath, 'r', encoding='utf-8') as f:
        movies_list = json.load(f)
    
    # Index by composite ID for fast lookup
    indexed_movies = {}
    for movie in movies_list:
        media_type = movie.get('media_type', 'movie')
        item_id = movie['id']
        composite_id = f"{media_type}_{item_id}"
        indexed_movies[composite_id] = movie
        
    return indexed_movies


def should_update_movie(existing: Dict, new: Dict) -> bool:
    """
    Determine if an existing movie should be updated.
    
    Movies are uniquely identified by TMDb ID, not title/year.
    This is because:
    - Same title can exist in different years (remakes)
    - Same title can exist in same year (different movies)
    
    Update if:
    1. Movie was upcoming and is now released
    2. Movie has more complete information now
    3. Movie data has been refreshed with better quality
    
    Args:
        existing: Existing movie data
        new: New movie data
    
    Returns:
        True if should update, False otherwise
    """
    # Movies are matched by TMDb ID, so this is the same movie
    # Check if we should update it with newer/better data
    
    # Check if movie transitioned from upcoming to released
    existing_date = existing.get('release_date', '')
    new_date = new.get('release_date', '')
    
    if existing_date and new_date:
        try:
            existing_dt = datetime.strptime(existing_date, '%Y-%m-%d')
            new_dt = datetime.strptime(new_date, '%Y-%m-%d')
            now = datetime.now()
            
            # Was upcoming, now released - definitely update
            if existing_dt > now and new_dt <= now:
                return True
        except:
            pass
    
    # Check if new data is more complete
    # (e.g., has cast/crew info that was missing before)
    existing_cast = len(existing.get('cast', []))
    new_cast = len(new.get('cast', []))
    
    existing_crew_total = (
        len(existing.get('director', [])) +
        len(existing.get('writers', [])) +
        len(existing.get('producers', []))
    )
    new_crew_total = (
        len(new.get('director', [])) +
        len(new.get('writers', [])) +
        len(new.get('producers', []))
    )
    
    # Update if new version has significantly more data (50% more)
    if new_cast > existing_cast * 1.5 or new_crew_total > existing_crew_total * 1.5:
        return True
    
    # Check if overview was empty and now has content
    if not existing.get('overview') and new.get('overview'):
        return True
    
    # Check if keywords were empty and now have content
    if not existing.get('keywords') and new.get('keywords'):
        return True
    
    # Check if reviews were empty and now have content
    if not existing.get('reviews') and new.get('reviews'):
        return True
    
    # Don't update if data is similar (avoid unnecessary updates)
    return False


def merge_movies(
    existing_movies: Dict[str, Dict],
    new_movies: List[Dict]
) -> tuple[List[Dict], Dict]:
    """
    Merge new media items with existing ones, preventing duplicates.
    
    IMPORTANT: Items are uniquely identified by (media_type + TMDb ID).
    
    Args:
        existing_movies: Dictionary of existing items by composite ID (type_id)
        new_movies: List of newly fetched items
    
    Returns:
        Tuple of (merged_list, statistics)
    """
    stats = {
        'total_existing': len(existing_movies),
        'total_new': len(new_movies),
        'added': 0,
        'updated': 0,
        'skipped': 0
    }
    
    merged = existing_movies.copy()
    
    for new_item in new_movies:
        # Create composite ID: "movie_123" or "tv_456"
        media_type = new_item.get('media_type', 'movie')
        item_id = new_item['id']
        composite_id = f"{media_type}_{item_id}"
        
        if composite_id in merged:
            # Same ID = same item, check if should update
            if should_update_movie(merged[composite_id], new_item):
                merged[composite_id] = new_item
                stats['updated'] += 1
                title = new_item.get('title') or new_item.get('name')
                date = new_item.get('release_date') or new_item.get('first_air_date', 'Unknown')
                print(f"  ✓ Updated: {title} ({date[:4]}) [{composite_id}]")
            else:
                stats['skipped'] += 1
        else:
            # New item
            merged[composite_id] = new_item
            stats['added'] += 1
            title = new_item.get('title') or new_item.get('name')
            date = new_item.get('release_date') or new_item.get('first_air_date', 'Unknown')
            print(f"  + Added: {title} ({date[:4]}) [{composite_id}]")
    
    # Convert back to list
    merged_list = list(merged.values())
    
    # Sort by date (newest first)
    def get_date(item):
        return item.get('release_date') or item.get('first_air_date') or '0000-00-00'
        
    merged_list.sort(key=get_date, reverse=True)
    
    stats['total_final'] = len(merged_list)
    
    return merged_list, stats


def save_movies(movies: List[Dict], filepath: str = "data/movies.json") -> None:
    """Save movies to JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(movies, f, indent=2, ensure_ascii=False)


def print_statistics(stats: Dict) -> None:
    """Print merge statistics."""
    print("\n" + "=" * 70)
    print("MERGE STATISTICS")
    print("=" * 70)
    print(f"Existing movies: {stats['total_existing']}")
    print(f"New movies fetched: {stats['total_new']}")
    print(f"Added: {stats['added']}")
    print(f"Updated: {stats['updated']}")
    print(f"Skipped (duplicates): {stats['skipped']}")
    print(f"Total in database: {stats['total_final']}")
    print("=" * 70)


if __name__ == "__main__":
    # Example usage
    print("Duplicate Prevention Utility")
    print("\nThis module is imported by collect_movies.py")
    print("Run collect_movies.py to use this functionality.")
