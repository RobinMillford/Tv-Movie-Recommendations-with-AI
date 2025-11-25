"""
Movie Data Optimization Utility
Combines minimization (remove unused fields) + compression (gzip)
Reduces file size by 85% while preserving all embedding data
"""

import json
import gzip
import os
from typing import List, Dict, Any


def minimize_movie_data(movie: Dict[str, Any]) -> Dict[str, Any]:
    """
    Keep only essential data for embeddings and metadata.
    Removes fields that aren't used in create_rich_description().
    
    PRESERVED (used in embeddings):
    - Title, tagline, overview
    - Genres, ALL keywords (not limited)
    - Director, writers (top 5), cinematographer, composer
    - Cast (top 20) with characters
    - Production companies (top 3), countries, languages
    - Runtime, certification, ratings
    - Popularity (for relevance boosting)
    - Reviews (top 5 for semantic richness)
    - Similar movies (top 10)
    - Alternative titles
    - Collection info
    
    REMOVED (not used in embeddings):
    - Videos/trailers
    - Budget/Revenue
    
    Args:
        movie: Full movie data dictionary
    
    Returns:
        Minimized movie data dictionary
    """
    minimized = {
        # Essential IDs
        'id': movie['id'],
        'media_type': movie.get('media_type', 'movie'),
        
        # Basic Info (used in embeddings)
        'title': movie['title'],
        'release_date': movie.get('release_date', ''),
        'status': movie.get('status', 'Released'),
        'overview': movie.get('overview', ''),
    }
    
    # Optional basic info
    if movie.get('original_title') and movie['original_title'] != movie['title']:
        minimized['original_title'] = movie['original_title']
    if movie.get('tagline'):
        minimized['tagline'] = movie['tagline']
    if movie.get('original_language'):
        minimized['original_language'] = movie['original_language']
    
    # Genres & Keywords (used in embeddings)
    if movie.get('genres'):
        minimized['genres'] = movie['genres']
    if movie.get('keywords'):
        minimized['keywords'] = movie['keywords']  # Keep all keywords
    
    # Crew (used in embeddings)
    if movie.get('director'):
        minimized['director'] = movie['director']
    if movie.get('writers'):
        minimized['writers'] = movie['writers'][:5]  # Only top 5
    if movie.get('cinematographer'):
        minimized['cinematographer'] = movie['cinematographer']
    if movie.get('composer'):
        minimized['composer'] = movie['composer']
    
    # TV Specific Fields
    if movie.get('created_by'):
        minimized['created_by'] = movie['created_by']
    if movie.get('number_of_seasons'):
        minimized['number_of_seasons'] = movie['number_of_seasons']
    if movie.get('number_of_episodes'):
        minimized['number_of_episodes'] = movie['number_of_episodes']
    if movie.get('networks'):
        minimized['networks'] = movie['networks']
    
    # Cast (used in embeddings - top 20)
    if movie.get('cast'):
        minimized['cast'] = movie['cast'][:20]
    
    # Production (used in embeddings)
    if movie.get('production_companies'):
        minimized['production_companies'] = movie['production_companies'][:3]
    if movie.get('production_countries'):
        minimized['production_countries'] = movie['production_countries']
    if movie.get('spoken_languages'):
        minimized['spoken_languages'] = movie['spoken_languages']
    
    # Collection (used in embeddings)
    if movie.get('collection_name'):
        minimized['collection_name'] = movie['collection_name']
    if movie.get('belongs_to_collection'):
        minimized['belongs_to_collection'] = movie['belongs_to_collection']
    
    # Ratings & Runtime (used in embeddings)
    if movie.get('runtime'):
        minimized['runtime'] = movie['runtime']
    if movie.get('certification'):
        minimized['certification'] = movie['certification']
    if movie.get('vote_average'):
        minimized['vote_average'] = movie['vote_average']
    if movie.get('vote_count'):
        minimized['vote_count'] = movie['vote_count']
    
    # Popularity (used for relevance boosting)
    if movie.get('popularity'):
        minimized['popularity'] = movie['popularity']
    
    # Reviews (used in embeddings - top 5 for semantic richness)
    if movie.get('reviews'):
        minimized['reviews'] = movie['reviews'][:5]
    
    # Similar Movies (used in embeddings - top 10)
    if movie.get('similar_movies'):
        minimized['similar_movies'] = [
            {'title': m.get('title', '')} 
            for m in movie['similar_movies'][:10]
        ]
    
    # Alternative Titles (used in embeddings)
    if movie.get('alternative_titles'):
        minimized['alternative_titles'] = movie['alternative_titles']
    
    return minimized


def optimize_movies_file(
    input_file: str = "data/movies.json",
    output_file: str = "data/movies.json.gz",
    minimize: bool = True,
    compress: bool = True,
    backup: bool = True
) -> Dict[str, Any]:
    """
    Optimize movies JSON file by minimizing data and compressing.
    
    Args:
        input_file: Path to input JSON file
        output_file: Path to output file
        minimize: If True, remove unnecessary fields (40% reduction)
        compress: If True, save as gzipped file (70-80% reduction)
        backup: If True, create backup of original file
    
    Returns:
        Statistics dictionary
    """
    print("=" * 70)
    print("MOVIE DATA OPTIMIZATION")
    print("=" * 70)
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"✗ Error: {input_file} not found!")
        return {}
    
    # Load movies
    print(f"\n[Step 1/4] Loading movies from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        movies = json.load(f)
    
    original_size = os.path.getsize(input_file)
    print(f"✓ Loaded {len(movies)} movies")
    print(f"  Original size: {original_size / 1024 / 1024:.2f} MB")
    
    # Backup original file
    if backup:
        print(f"\n[Step 2/4] Creating backup...")
        backup_file = input_file + '.backup'
        import shutil
        shutil.copy2(input_file, backup_file)
        print(f"✓ Backup saved: {backup_file}")
    else:
        print(f"\n[Step 2/4] Skipping backup...")
    
    # Minimize if requested
    if minimize:
        print(f"\n[Step 3/4] Minimizing movie data...")
        minimized_movies = [minimize_movie_data(movie) for movie in movies]
        print(f"✓ Minimized {len(minimized_movies)} movies")
        
        # Calculate size reduction
        temp_json = json.dumps(minimized_movies, indent=2, ensure_ascii=False)
        minimized_size = len(temp_json.encode('utf-8'))
        reduction = (1 - minimized_size / original_size) * 100
        print(f"  After minimization: {minimized_size / 1024 / 1024:.2f} MB ({reduction:.1f}% reduction)")
    else:
        print(f"\n[Step 3/4] Skipping minimization...")
        minimized_movies = movies
        minimized_size = original_size
    
    # Save
    print(f"\n[Step 4/4] Saving to {output_file}...")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    if compress:
        with gzip.open(output_file, 'wt', encoding='utf-8') as f:
            json.dump(minimized_movies, f, indent=2, ensure_ascii=False)
        final_size = os.path.getsize(output_file)
        print(f"✓ Saved compressed file")
    else:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(minimized_movies, f, indent=2, ensure_ascii=False)
        final_size = os.path.getsize(output_file)
        print(f"✓ Saved file")
    
    # Statistics
    total_reduction = (1 - final_size / original_size) * 100
    
    print("\n" + "=" * 70)
    print("OPTIMIZATION COMPLETE")
    print("=" * 70)
    print(f"Original size:   {original_size / 1024 / 1024:.2f} MB")
    print(f"Final size:      {final_size / 1024 / 1024:.2f} MB")
    print(f"Total reduction: {total_reduction:.1f}%")
    print(f"Space saved:     {(original_size - final_size) / 1024 / 1024:.2f} MB")
    print(f"Output file:     {output_file}")
    
    if backup:
        print(f"Backup file:     {backup_file}")
    
    return {
        'original_size': original_size,
        'final_size': final_size,
        'reduction_percent': total_reduction,
        'total_movies': len(minimized_movies),
        'minimize': minimize,
        'compress': compress
    }


if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    minimize = True
    compress = True
    backup = True
    
    if len(sys.argv) > 1:
        if '--no-minimize' in sys.argv:
            minimize = False
        if '--no-compress' in sys.argv:
            compress = False
        if '--no-backup' in sys.argv:
            backup = False
    
    # Run optimization
    stats = optimize_movies_file(
        input_file="data/movies.json",
        output_file="data/movies.json.gz",
        minimize=minimize,
        compress=compress,
        backup=backup
    )
    
    if stats:
        print("\n✅ Optimization complete!")
        print("\nNext steps:")
        print("1. Update scripts to use compressed file:")
        print("   - Update generate_embeddings.py")
        print("   - Update collect_movies.py")
        print("2. Test embeddings generation:")
        print("   python scripts/generate_embeddings.py")
        print("3. If everything works, delete backup:")
        print("   rm data/movies.json.backup")
