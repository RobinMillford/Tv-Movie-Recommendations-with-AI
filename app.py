from flask import Flask, render_template, request
import requests
import time
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

TMDB_API_KEY = os.getenv("TMDB_API_KEY")

# Helper function to fetch movies by genre
def fetch_movies_by_genre(genre_id, max_movies=50):
    url = f"https://api.themoviedb.org/3/discover/movie?api_key={TMDB_API_KEY}&with_genres={genre_id}&sort_by=popularity.desc&page=1"
    response = requests.get(url)
    data = response.json()
    return data.get('results', [])[:max_movies]

# Helper function to fetch TV shows by genre
def fetch_shows_by_genre(genre_id, max_shows=50):
    url = f"https://api.themoviedb.org/3/discover/tv?api_key={TMDB_API_KEY}&with_genres={genre_id}&sort_by=popularity.desc&page=1"
    response = requests.get(url)
    data = response.json()
    return data.get('results', [])[:max_shows]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/tv_shows')
def tv_shows():
    return render_template('tv_shows.html')

@app.route('/genre/<genre_name>')
def genre_page(genre_name):
    genre_mapping = {
        'romance': 10749,
        'horror': 27,
        'fantasy': 14,
        'science_fiction': 878,
        'mystery': 9648,
        'western': 37,
        'drama': 18,
        'action': 28,
        'comedy': 35,
        'thriller': 53,
        'adventure': 12,
        'animation': 16,
        'crime': 80,
        'family': 10751,
        'history': 36,
        'music': 10402,
        'war': 10752,
        'documentary': 99,
        'tv_movie': 10770
    }
    genre_id = genre_mapping.get(genre_name)

    if genre_id:
        movies = fetch_movies_by_genre(genre_id)
        return render_template('genre.html', genre_name=genre_name.capitalize(), movies=movies)
    else:
        return render_template('genre_not_found.html', genre_name=genre_name.capitalize())

@app.route('/tv_genre/<genre_name>')
def tv_genre_page(genre_name):
    genre_mapping = {
        'action_adventure': 10759,
        'animation': 16,
        'comedy': 35,
        'crime': 80,
        'documentary': 99,
        'drama': 18,
        'family': 10751,
        'kids': 10762,
        'mystery': 9648,
        'news': 10763,
        'reality': 10764,
        'sci_fi_fantasy': 10765,
        'soap': 10766,
        'talk': 10767,
        'war_politics': 10768,
        'western': 37
    }
    genre_id = genre_mapping.get(genre_name)

    if genre_id:
        shows = fetch_shows_by_genre(genre_id)
        return render_template('tv_genre.html', genre_name=genre_name.replace('_', ' ').capitalize(), shows=shows)
    else:
        return render_template('genre_not_found.html', genre_name=genre_name.replace('_', ' ').capitalize())

@app.route('/recommend', methods=['POST'])
def recommend():
    movie_name = request.form['movie_name']
    tmdb_search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&language=en-US&query={movie_name}&page=1&include_adult=true"
    response = requests.get(tmdb_search_url)
    data = response.json()
    tmdb_results = data.get('results', [])
    
    if tmdb_results:
        searched_movie = tmdb_results[0]
        searched_movie_id = searched_movie['id']
        searched_movie_poster = fetch_poster(searched_movie_id)
        
        tmdb_recommendations = fetch_tmdb_recommendations(searched_movie_id)
        
        recommend_movie = []
        recommend_poster = []
        tmdb_links = []
        
        for rec in tmdb_recommendations:
            if rec['id'] != searched_movie_id:
                recommend_movie.append(rec['title'])
                recommend_poster.append(fetch_poster(rec['id']))
                tmdb_links.append(f"https://www.themoviedb.org/movie/{rec['id']}/")

        return render_template('recommend.html', searched_movie=movie_name, searched_movie_poster=searched_movie_poster,
                               recommend_movie=recommend_movie, recommend_poster=recommend_poster, tmdb_links=tmdb_links)
    else:
        return render_template('no_results.html', searched_movie=movie_name)

@app.route('/tv_recommend', methods=['POST'])
def tv_recommend():
    show_name = request.form['show_name']
    tmdb_search_url = f"https://api.themoviedb.org/3/search/tv?api_key={TMDB_API_KEY}&language=en-US&query={show_name}&page=1&include_adult=true"
    response = requests.get(tmdb_search_url)
    data = response.json()
    tmdb_results = data.get('results', [])
    
    if tmdb_results:
        searched_show = tmdb_results[0]
        searched_show_id = searched_show['id']
        searched_show_poster = fetch_poster(searched_show_id, is_movie=False)
        
        tmdb_recommendations = fetch_tmdb_recommendations(searched_show_id, is_movie=False)
        
        recommend_show = []
        recommend_poster = []
        tmdb_links = []
        
        for rec in tmdb_recommendations:
            if rec['id'] != searched_show_id:
                recommend_show.append(rec['name'])
                recommend_poster.append(fetch_poster(rec['id'], is_movie=False))
                tmdb_links.append(f"https://www.themoviedb.org/tv/{rec['id']}/")

        return render_template('tv_recommend.html', searched_show=show_name, searched_show_poster=searched_show_poster,
                               recommend_show=recommend_show, recommend_poster=recommend_poster, tmdb_links=tmdb_links)
    else:
        return render_template('no_results.html', searched_show=show_name)

def fetch_poster(id, is_movie=True, max_retries=3, retry_delay=1):
    media_type = "movie" if is_movie else "tv"
    url = f"https://api.themoviedb.org/3/{media_type}/{id}?api_key={TMDB_API_KEY}&language=en-US"
    
    for _ in range(max_retries):
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            poster_path = data.get('poster_path')
            if poster_path:
                return f"https://image.tmdb.org/t/p/w500/{poster_path}"
            return None
        except (requests.exceptions.RequestException, requests.exceptions.Timeout) as e:
            print(f"Error fetching poster: {e}. Retrying...")
            time.sleep(retry_delay)
    
    raise Exception("Failed to fetch poster after multiple retries.")

def fetch_tmdb_recommendations(id, is_movie=True, max_recommendations=50):
    media_type = "movie" if is_movie else "tv"
    url = f"https://api.themoviedb.org/3/{media_type}/{id}/recommendations?api_key={TMDB_API_KEY}&language=en-US&page=1"
    response = requests.get(url)
    data = response.json()
    recommendations = data.get('results', [])
    return recommendations[:max_recommendations]

if __name__ == '__main__':
    app.run(host="0.0.0.0",port=5000)
