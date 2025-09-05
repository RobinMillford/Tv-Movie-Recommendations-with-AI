from flask import Blueprint, render_template, request, jsonify
import requests
import time
import os
from api.tmdb_client import (
    fetch_now_playing_movies, fetch_popular_movies, fetch_upcoming_movies,
    fetch_trending_people, fetch_airing_today_shows, fetch_on_the_air_shows,
    fetch_popular_shows, fetch_trending_movies, fetch_movies_by_genre,
    fetch_shows_by_genre, fetch_poster, fetch_tmdb_recommendations
)

# Get environment variables
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_API_KEY_2 = os.getenv("TMDB_API_KEY_2")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

main = Blueprint('main', __name__)

@main.route('/')
def index():
    trending_backdrops = fetch_trending_movies()
    now_playing = fetch_now_playing_movies()
    popular = fetch_popular_movies()
    # Get IDs from now_playing and popular to exclude
    exclude_ids = {movie['id'] for movie in now_playing + popular}
    upcoming = fetch_upcoming_movies(exclude_ids=exclude_ids)
    airing_today = fetch_airing_today_shows()
    on_the_air = fetch_on_the_air_shows()
    popular_shows = fetch_popular_shows()
    trending_people = fetch_trending_people()
    return render_template(
        'index.html',
        trending_backdrops=trending_backdrops,
        now_playing=now_playing,
        popular=popular,
        upcoming=upcoming,
        airing_today=airing_today,
        on_the_air=on_the_air,
        popular_shows=popular_shows,
        trending_people=trending_people
    )

@main.route('/search', methods=['POST'])
def search():
    query = request.form.get('query')
    if not query:
        return render_template('index.html', error="Please enter a search term.")

    # Search movies
    movie_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&language=en-US&query={query}&page=1"
    movie_response = requests.get(movie_url)
    movie_data = movie_response.json().get('results', [])

    # Search TV shows
    tv_url = f"https://api.themoviedb.org/3/search/tv?api_key={TMDB_API_KEY}&language=en-US&query={query}&page=1"
    tv_response = requests.get(tv_url)
    tv_data = tv_response.json().get('results', [])

    # Search people
    person_url = f"https://api.themoviedb.org/3/search/person?api_key={TMDB_API_KEY}&language=en-US&query={query}&page=1"
    person_response = requests.get(person_url)
    person_data = person_response.json().get('results', [])

    # Format all results, filtering out items without images
    movies = [
        {
            'id': m['id'],
            'title': m['title'],
            'release_date': m.get('release_date', 'N/A'),
            'poster_path': m.get('poster_path')
        } for m in movie_data if m.get('poster_path')
    ]
    shows = [
        {
            'id': s['id'],
            'name': s['name'],
            'first_air_date': s.get('first_air_date', 'N/A'),
            'poster_path': s.get('poster_path')
        } for s in tv_data if s.get('poster_path')
    ]
    people = [
        {
            'id': p['id'],
            'name': p['name'],
            'known_for': p.get('known_for_department', 'N/A'),
            'profile_path': p.get('profile_path')
        } for p in person_data if p.get('profile_path')
    ]

    return render_template('search_results.html', query=query, movies=movies, shows=shows, people=people)

@main.route('/autocomplete')
def autocomplete():
    query = request.args.get('query', '')
    if not query:
        return jsonify({'movies': [], 'shows': [], 'people': []})

    # Search movies
    movie_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&language=en-US&query={query}&page=1"
    movie_response = requests.get(movie_url)
    movie_data = movie_response.json().get('results', [])

    # Search TV shows
    tv_url = f"https://api.themoviedb.org/3/search/tv?api_key={TMDB_API_KEY}&language=en-US&query={query}&page=1"
    tv_response = requests.get(tv_url)
    tv_data = tv_response.json().get('results', [])

    # Search people
    person_url = f"https://api.themoviedb.org/3/search/person?api_key={TMDB_API_KEY}&language=en-US&query={query}&page=1"
    person_response = requests.get(person_url)
    person_data = person_response.json().get('results', [])

    # Format results, filtering out items without images (limit 5 each)
    movies = [{'id': m['id'], 'title': m['title'], 'release_date': m.get('release_date'), 'poster_path': m.get('poster_path')} 
              for m in movie_data if m.get('poster_path')][:5]
    shows = [{'id': s['id'], 'name': s['name'], 'first_air_date': s.get('first_air_date'), 'poster_path': s.get('poster_path')} 
             for s in tv_data if s.get('poster_path')][:5]
    people = [{'id': p['id'], 'name': p['name'], 'known_for': p.get('known_for_department'), 'profile_path': p.get('profile_path')} 
              for p in person_data if p.get('profile_path')][:5]

    return jsonify({'movies': movies, 'shows': shows, 'people': people})

@main.route('/news')
def news():
    # NewsAPI call with refined query
    news_url = (
        f"https://newsapi.org/v2/everything?"
        f"q=movies OR 'TV shows' OR 'movie actors' OR 'TV actors' OR actresses "
        f"-sports -politics -business -tech "
        f"&apiKey={NEWS_API_KEY}&language=en&sortBy=publishedAt&pageSize=50"
    )
    news_response = requests.get(news_url)
    news_data = news_response.json()
    articles = news_data.get('articles', [])
    filtered_articles = [
        {
            'title': article['title'],
            'description': article['description'] or 'No description available',
            'url': article['url'],
            'urlToImage': article['urlToImage'],
            'publishedAt': article['publishedAt']
        } for article in articles 
        if article.get('title') and article.get('url') and article.get('urlToImage') and  # Require image
           any(keyword in article['title'].lower() or keyword in (article['description'] or '').lower() 
               for keyword in ['movie', 'tv', 'actor', 'actress', 'show', 'film', 'series', 'cinema', 
                               'television', 'star', 'celebrity', 'director', 'producer', 'screenplay', 
                               'premiere', 'release', 'cast', 'episode', 'season'])
    ]
    return render_template('news.html', articles=filtered_articles)

@main.route('/movies')
def movies():
    return render_template('movies.html', api_key=TMDB_API_KEY_2)

@main.route('/tv_shows')
def tv_shows():
    return render_template('tv_shows.html', api_key=TMDB_API_KEY_2)

@main.route('/genre/<genre_name>')
def genre_page(genre_name):
    genre_mapping = {
        'romance': 10749, 'horror': 27, 'fantasy': 14, 'science_fiction': 878, 'mystery': 9648,
        'western': 37, 'drama': 18, 'action': 28, 'comedy': 35, 'thriller': 53, 'adventure': 12,
        'animation': 16, 'crime': 80, 'family': 10751, 'history': 36, 'music': 10402, 'war': 10752,
        'documentary': 99, 'tv_movie': 10770
    }
    genre_id = genre_mapping.get(genre_name)
    if genre_id:
        movies = fetch_movies_by_genre(genre_id)
        return render_template('genre.html', genre_name=genre_name.capitalize(), movies=movies)
    else:
        return render_template('genre_not_found.html', genre_name=genre_name.capitalize())

@main.route('/tv_genre/<genre_name>')
def tv_genre_page(genre_name):
    genre_mapping = {
        'action_adventure': 10759, 'animation': 16, 'comedy': 35, 'crime': 80, 'documentary': 99,
        'drama': 18, 'family': 10751, 'kids': 10762, 'mystery': 9648, 'news': 10763, 'reality': 10764,
        'sci_fi_fantasy': 10765, 'soap': 10766, 'talk': 10767, 'war_politics': 10768, 'western': 37
    }
    genre_id = genre_mapping.get(genre_name)
    if genre_id:
        shows = fetch_shows_by_genre(genre_id)
        return render_template('tv_genre.html', genre_name=genre_name.replace('_', ' ').capitalize(), shows=shows)
    else:
        return render_template('genre_not_found.html', genre_name=genre_name.replace('_', ' ').capitalize())

@main.route('/recommend', methods=['POST'])
def recommend():
    movie_name = request.form['movie_name']
    tmdb_search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&language=en-US&query={movie_name}&page=1&include_adult=true"
    time.sleep(1)
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
        recommend_ids = []  # New list to store movie IDs
        
        for rec in tmdb_recommendations:
            if rec['id'] != searched_movie_id:
                recommend_movie.append(rec['title'])
                recommend_poster.append(fetch_poster(rec['id']))
                recommend_ids.append(rec['id'])  # Store the movie ID

        return render_template('recommend.html', 
                               searched_movie=movie_name, 
                               searched_movie_poster=searched_movie_poster,
                               recommend_movie=recommend_movie, 
                               recommend_poster=recommend_poster, 
                               recommend_ids=recommend_ids)  # Pass the IDs to the template
    else:
        return render_template('no_results.html', searched_movie=movie_name)

@main.route('/tv_recommend', methods=['POST'])
def tv_recommend():
    show_name = request.form['show_name']
    tmdb_search_url = f"https://api.themoviedb.org/3/search/tv?api_key={TMDB_API_KEY}&language=en-US&query={show_name}&page=1&include_adult=true"
    time.sleep(1)
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
        recommend_ids = []  # New list to store TV show IDs
        
        for rec in tmdb_recommendations:
            if rec['id'] != searched_show_id:
                recommend_show.append(rec['name'])
                recommend_poster.append(fetch_poster(rec['id'], is_movie=False))
                recommend_ids.append(rec['id'])  # Store the TV show ID

        return render_template('tv_recommend.html', 
                               searched_show=show_name, 
                               searched_show_poster=searched_show_poster,
                               recommend_show=recommend_show, 
                               recommend_poster=recommend_poster, 
                               recommend_ids=recommend_ids)  # Pass the IDs to the template
    else:
        return render_template('no_results.html', searched_show=show_name)