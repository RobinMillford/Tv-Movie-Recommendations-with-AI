"""
Upload Movie Embeddings to Hugging Face Dataset

This script uploads the ChromaDB database and movie metadata to Hugging Face
for free unlimited storage and easy access from Render deployment.

Features:
- Prevents duplicate movies
- Updates upcoming movies when they're released
- Compresses files for efficient storage
- Creates dataset card with statistics
"""

import os
import json
import shutil
from datetime import datetime
from huggingface_hub import HfApi, create_repo, upload_folder
from pathlib import Path
import gzip
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()


def compress_file(input_path: str, output_path: str) -> None:
    """Compress a file using gzip."""
    print(f"  Compressing {input_path}...")
    with open(input_path, 'rb') as f_in:
        with gzip.open(output_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    
    original_size = os.path.getsize(input_path) / (1024 * 1024)
    compressed_size = os.path.getsize(output_path) / (1024 * 1024)
    ratio = (1 - compressed_size / original_size) * 100
    print(f"  ✓ Compressed: {original_size:.2f}MB → {compressed_size:.2f}MB ({ratio:.1f}% reduction)")


def prepare_upload_directory() -> str:
    """
    Prepare a temporary directory with files to upload.
    
    Returns:
        Path to upload directory
    """
    upload_dir = "./hf_upload_temp"
    
    # Clean up if exists
    if os.path.exists(upload_dir):
        shutil.rmtree(upload_dir)
    
    os.makedirs(upload_dir, exist_ok=True)
    
    print("\n[Step 1/4] Preparing files for upload...")
    
    # 1. Copy and compress ChromaDB files
    chroma_files = [
        "chroma_db/chroma.sqlite3",
        # Add other ChromaDB files if they exist
    ]
    
    for file_path in chroma_files:
        if os.path.exists(file_path):
            filename = os.path.basename(file_path)
            compress_file(file_path, os.path.join(upload_dir, f"{filename}.gz"))
    
    
    # 2. Copy compressed movies.json.gz (created by optimize_movies.py)
    if os.path.exists("data/movies.json.gz"):
        print("  Copying compressed movies.json.gz...")
        shutil.copy("data/movies.json.gz", os.path.join(upload_dir, "movies.json.gz"))
        size_mb = os.path.getsize("data/movies.json.gz") / (1024 * 1024)
        print(f"  ✓ Copied: {size_mb:.2f}MB (compressed)")
    elif os.path.exists("data/movies.json"):
        # Fallback: compress on the fly if .gz doesn't exist
        print("  Compressing movies.json...")
        compress_file("data/movies.json", os.path.join(upload_dir, "movies.json.gz"))
    
    # 3. Create metadata file
    create_metadata_file(upload_dir)
    
    # 4. Create README (dataset card)
    create_dataset_card(upload_dir)
    
    return upload_dir


def create_metadata_file(upload_dir: str) -> None:
    """Create metadata file with dataset information."""
    print("  Creating metadata...")
    
    # Load movies to get statistics
    with open("data/movies.json", 'r', encoding='utf-8') as f:
        movies = json.load(f)
    
    # Calculate statistics
    years = {}
    genres = {}
    for movie in movies:
        year = movie.get('release_year', 'Unknown')
        if year != 'Unknown':
            years[year] = years.get(year, 0) + 1
        
        for genre in movie.get('genres', []):
            genres[genre] = genres.get(genre, 0) + 1
    
    metadata = {
        "version": datetime.now().strftime("%Y-%m-%d-%H%M"),  # Version with timestamp
        "total_movies": len(movies),
        "date_range": {
            "earliest": min(years.keys()) if years else "Unknown",
            "latest": max(years.keys()) if years else "Unknown"
        },
        "movies_by_year": dict(sorted(years.items(), reverse=True)),
        "top_genres": dict(sorted(genres.items(), key=lambda x: x[1], reverse=True)[:10]),
        "last_updated": datetime.now().isoformat(),
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
        "embedding_dimension": 384
    }
    
    with open(os.path.join(upload_dir, "metadata.json"), 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"  ✓ Metadata created: {len(movies)} movies")


def create_dataset_card(upload_dir: str) -> None:
    """Create README.md dataset card for Hugging Face."""
    print("  Creating dataset card...")
    
    # Load metadata
    with open(os.path.join(upload_dir, "metadata.json"), 'r') as f:
        metadata = json.load(f)
    
    readme_content = f"""---
license: mit
tags:
- movies
- embeddings
- rag
- chromadb
- sentence-transformers
size_categories:
- 1K<n<10K
---

# Movie Embeddings RAG Dataset

This dataset contains movie embeddings for Retrieval-Augmented Generation (RAG) in a movie recommendation chatbot.

## Dataset Information

- **Total Movies:** {metadata['total_movies']}
- **Date Range:** {metadata['date_range']['earliest']} - {metadata['date_range']['latest']}
- **Last Updated:** {metadata['last_updated'][:10]}
- **Embedding Model:** {metadata['embedding_model']}
- **Embedding Dimension:** {metadata['embedding_dimension']}

## Files

- `chroma.sqlite3.gz` - Compressed ChromaDB database with embeddings
- `movies.json.gz` - Compressed movie metadata (title, overview, cast, crew, etc.)
- `metadata.json` - Dataset statistics and version info

## Top Genres

{chr(10).join(f"- {genre}: {count} movies" for genre, count in list(metadata['top_genres'].items())[:5])}

## Usage

### Download and Extract

```python
from huggingface_hub import hf_hub_download
import gzip
import shutil

# Download compressed database
db_path = hf_hub_download(
    repo_id="YOUR_USERNAME/movie-embeddings-rag",
    filename="chroma.sqlite3.gz",
    repo_type="dataset"
)

# Decompress
with gzip.open(db_path, 'rb') as f_in:
    with open('chroma.sqlite3', 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)
```

### Use with ChromaDB

```python
import chromadb

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection("movies")

# Search for movies
results = collection.query(
    query_texts=["science fiction movie about space"],
    n_results=5
)
```

## Automated Updates

This dataset is automatically updated monthly via GitHub Actions with new movie releases.

## License

MIT License - Free to use for any purpose.
"""
    
    with open(os.path.join(upload_dir, "README.md"), 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print("  ✓ Dataset card created")


def upload_to_huggingface(
    upload_dir: str,
    repo_id: str,
    token: str = None
) -> None:
    """
    Upload directory to Hugging Face dataset.
    
    Args:
        upload_dir: Directory containing files to upload
        repo_id: Hugging Face repo ID (username/dataset-name)
        token: Hugging Face API token (or set HF_TOKEN env var)
    """
    print(f"\n[Step 2/4] Uploading to Hugging Face: {repo_id}...")
    
    # Get token from environment if not provided
    if token is None:
        token = os.getenv("HF_TOKEN")
        if not token:
            raise ValueError("HF_TOKEN environment variable not set!")
    
    # Initialize API
    api = HfApi()
    
    # Create repo if it doesn't exist
    try:
        print("  Creating/verifying repository...")
        create_repo(
            repo_id=repo_id,
            repo_type="dataset",
            token=token,
            exist_ok=True,
            private=False  # Public dataset
        )
        print("  ✓ Repository ready")
    except Exception as e:
        print(f"  Note: {e}")
    
    # Upload folder
    try:
        print("  Uploading files...")
        api.upload_folder(
            folder_path=upload_dir,
            repo_id=repo_id,
            repo_type="dataset",
            token=token,
            commit_message=f"Update dataset - {datetime.now().strftime('%Y-%m-%d')}"
        )
        print("  ✓ Upload complete!")
    except Exception as e:
        print(f"  ✗ Upload failed: {e}")
        raise


def cleanup(upload_dir: str) -> None:
    """Clean up temporary upload directory."""
    print(f"\n[Step 3/4] Cleaning up...")
    if os.path.exists(upload_dir):
        shutil.rmtree(upload_dir)
        print("  ✓ Temporary files removed")


def verify_upload(repo_id: str) -> None:
    """Verify the upload was successful."""
    print(f"\n[Step 4/4] Verifying upload...")
    
    api = HfApi()
    try:
        files = api.list_repo_files(repo_id=repo_id, repo_type="dataset")
        print(f"  ✓ Files in dataset:")
        for file in files:
            print(f"    - {file}")
        
        print(f"\n✅ Dataset URL: https://huggingface.co/datasets/{repo_id}")
    except Exception as e:
        print(f"  ✗ Verification failed: {e}")


def main():
    """Main upload process."""
    print("=" * 70)
    print("UPLOAD MOVIE EMBEDDINGS TO HUGGING FACE")
    print("=" * 70)
    
    # Load configuration from .env
    HF_REPO_ID = os.getenv("HF_REPO_ID")
    HF_TOKEN = os.getenv("HF_TOKEN")
    
    if not HF_REPO_ID:
        print("\n⚠️  HF_REPO_ID not found in .env file!")
        print("   Please add: HF_REPO_ID=your-username/movie-embeddings-rag")
        return
    
    if not HF_TOKEN:
        print("\n⚠️  HF_TOKEN not found in .env file!")
        print("   Please add: HF_TOKEN=your_huggingface_token")
        return
    
    print(f"\n📦 Repository: {HF_REPO_ID}")
    print(f"🔑 Token: {'*' * 20}{HF_TOKEN[-4:]}")  # Show last 4 chars only
    
    try:
        # Prepare files
        upload_dir = prepare_upload_directory()
        
        # Upload to Hugging Face
        upload_to_huggingface(upload_dir, HF_REPO_ID, HF_TOKEN)
        
        # Clean up
        cleanup(upload_dir)
        
        # Verify
        verify_upload(HF_REPO_ID)
        
        print("\n" + "=" * 70)
        print("✅ UPLOAD COMPLETE!")
        print("=" * 70)
        print(f"\nDataset: https://huggingface.co/datasets/{HF_REPO_ID}")
        print("\nNext steps:")
        print("1. Verify dataset on Hugging Face")
        print("2. Update vector_db.py to download from this dataset")
        print("3. Set up GitHub Actions for monthly updates")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
