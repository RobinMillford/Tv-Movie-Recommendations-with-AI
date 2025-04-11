from flask import Flask, render_template, request, jsonify
import requests
import time
from dotenv import load_dotenv
import os
from langchain_groq import ChatGroq
from langchain.schema import AIMessage, HumanMessage
from langchain.prompts import PromptTemplate
import json
import re
import hashlib  # For Gravatar hash
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_API_KEY_2 = os.getenv("TMDB_API_KEY_2")
GROQ_API_KEY = os.getenv("groq_api_key")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

chatbot = ChatGroq(model_name="llama3-70b-8192", api_key=GROQ_API_KEY)

prompt_template = PromptTemplate(
    input_variables=["chat_history", "user_input"],
    template="You are a helpful movie recommendation assistant. Here is the conversation so far:\n{chat_history}\nUser: {user_input}\nAssistant:"
)

conversation_chain = prompt_template | chatbot

def fetch_now_playing_movies(max_movies=18):
    url = f"https://api.themoviedb.org/3/movie/now_playing?api_key={TMDB_API_KEY}&language=en-US&page=1"
    response = requests.get(url)
    data = response.json()
    results = data.get('results', [])
    filtered_results = [movie for movie in results if movie.get('poster_path') and movie.get('title')]
    return [
        {
            'id': movie['id'],
            'title': movie['title'],
            'release_date': movie.get('release_date', 'N/A'),
            'poster_path': f"https://image.tmdb.org/t/p/w500{movie['poster_path']}"
        } for movie in filtered_results[:max_movies]
    ]

def fetch_popular_movies(max_movies=18):
    url = f"https://api.themoviedb.org/3/movie/popular?api_key={TMDB_API_KEY}&language=en-US&page=1"
    response = requests.get(url)
    data = response.json()
    results = data.get('results', [])
    filtered_results = [movie for movie in results if movie.get('poster_path') and movie.get('title')]
    return [
        {
            'id': movie['id'],
            'title': movie['title'],
            'release_date': movie.get('release_date', 'N/A'),
            'poster_path': f"https://image.tmdb.org/t/p/w500{movie['poster_path']}"
        } for movie in filtered_results[:max_movies]
    ]

def fetch_upcoming_movies(max_movies=18, exclude_ids=None, current_year=None):
    if exclude_ids is None:
        exclude_ids = set()
    if current_year is None:
        current_year = datetime.now().year  # 2025 as of April 11, 2025

    url = f"https://api.themoviedb.org/3/movie/upcoming?api_key={TMDB_API_KEY}&language=en-US&page=1"
    response = requests.get(url)
    data = response.json()
    results = data.get('results', [])
    filtered_results = [
        movie for movie in results 
        if movie.get('poster_path') and movie.get('title') and 
           movie['id'] not in exclude_ids and  # Exclude movies from now_playing and popular
           movie.get('release_date', '').startswith(str(current_year))  # Only current year
    ]
    return [
        {
            'id': movie['id'],
            'title': movie['title'],
            'release_date': movie.get('release_date', 'N/A'),
            'poster_path': f"https://image.tmdb.org/t/p/w500{movie['poster_path']}"
        } for movie in filtered_results[:max_movies]
    ]

def fetch_trending_people(time_window='week', max_people=18):
    url = f"https://api.themoviedb.org/3/trending/person/{time_window}?api_key={TMDB_API_KEY}"
    response = requests.get(url)
    data = response.json()
    results = data.get('results', [])
    filtered_results = [person for person in results if person.get('profile_path') and person.get('name')]
    return [
        {
            'id': person['id'],
            'name': person['name'],
            'known_for_department': person.get('known_for_department', 'N/A'),
            'profile_path': f"https://image.tmdb.org/t/p/w500{person['profile_path']}"
        } for person in filtered_results[:max_people]
    ]

def fetch_airing_today_shows(max_shows=18):
    url = f"https://api.themoviedb.org/3/tv/airing_today?api_key={TMDB_API_KEY}&language=en-US&page=1"
    response = requests.get(url)
    data = response.json()
    results = data.get('results', [])
    filtered_results = [show for show in results if show.get('poster_path') and show.get('name')]
    return [
        {
            'id': show['id'],
            'name': show['name'],
            'first_air_date': show.get('first_air_date', 'N/A'),
            'poster_path': f"https://image.tmdb.org/t/p/w500{show['poster_path']}"
        } for show in filtered_results[:max_shows]
    ]

def fetch_on_the_air_shows(max_shows=18):
    url = f"https://api.themoviedb.org/3/tv/on_the_air?api_key={TMDB_API_KEY}&language=en-US&page=1"
    response = requests.get(url)
    data = response.json()
    results = data.get('results', [])
    filtered_results = [show for show in results if show.get('poster_path') and show.get('name')]
    return [
        {
            'id': show['id'],
            'name': show['name'],
            'first_air_date': show.get('first_air_date', 'N/A'),
            'poster_path': f"https://image.tmdb.org/t/p/w500{show['poster_path']}"
        } for show in filtered_results[:max_shows]
    ]

def fetch_popular_shows(max_shows=18):
    url = f"https://api.themoviedb.org/3/tv/popular?api_key={TMDB_API_KEY}&language=en-US&page=1"
    response = requests.get(url)
    data = response.json()
    results = data.get('results', [])
    filtered_results = [show for show in results if show.get('poster_path') and show.get('name')]
    return [
        {
            'id': show['id'],
            'name': show['name'],
            'first_air_date': show.get('first_air_date', 'N/A'),
            'poster_path': f"https://image.tmdb.org/t/p/w500{show['poster_path']}"
        } for show in filtered_results[:max_shows]
    ]

# Updated Index Route
@app.route('/')
def index():
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
        now_playing=now_playing,
        popular=popular,
        upcoming=upcoming,
        airing_today=airing_today,
        on_the_air=on_the_air,
        popular_shows=popular_shows,
        trending_people=trending_people
    )

@app.route('/search', methods=['POST'])
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

@app.route('/autocomplete')
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

@app.route('/news')
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

@app.route('/movies')
def movies():
    return render_template('movies.html', api_key=TMDB_API_KEY_2)

@app.route('/tv_shows')
def tv_shows():
    return render_template('tv_shows.html', api_key=TMDB_API_KEY_2)

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

@app.route('/genre/<genre_name>')
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

@app.route('/tv_genre/<genre_name>')
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

@app.route('/recommend', methods=['POST'])
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

@app.route('/tv_recommend', methods=['POST'])
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

def fetch_poster(id, is_movie=True, max_retries=3, retry_delay=2):
    media_type = "movie" if is_movie else "tv"
    url = f"https://api.themoviedb.org/3/{media_type}/{id}?api_key={TMDB_API_KEY}&language=en-US"
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            poster_path = data.get('poster_path')
            return f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else "https://via.placeholder.com/500x750?text=No+Image"
        except requests.exceptions.RequestException as e:
            print(f"Error fetching poster (attempt {attempt + 1}/{max_retries}): {e}")
            time.sleep(retry_delay)
    print(f"Failed to fetch poster for {media_type}/{id} after {max_retries} retries.")
    return "https://via.placeholder.com/500x750?text=No+Image"

def fetch_tmdb_recommendations(id, is_movie=True, max_recommendations=50):
    media_type = "movie" if is_movie else "tv"
    url = f"https://api.themoviedb.org/3/{media_type}/{id}/recommendations?api_key={TMDB_API_KEY}&language=en-US&page=1"
    time.sleep(1)
    response = requests.get(url)
    data = response.json()
    return data.get('results', [])[:max_recommendations]

@app.route("/chat")
def chat():
    return render_template("chat.html")

chat_sessions = {}

@app.route("/chat_api", methods=["POST"])
def chat_api():
    user_message = request.json.get("message")
    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    session_id = request.remote_addr
    if session_id not in chat_sessions:
        chat_sessions[session_id] = []

    formatted_history = [
        HumanMessage(content=msg["content"]) if msg["type"] == "human" else AIMessage(content=msg["content"])
        for msg in chat_sessions[session_id]
    ]
    formatted_history.append(HumanMessage(content=user_message))

    bot_response = conversation_chain.invoke({"chat_history": formatted_history, "user_input": user_message})
    bot_reply = bot_response.content.strip()

    if not bot_reply:
        return jsonify({"error": "Bot response is empty. Please try again."}), 500

    formatted_history.append(AIMessage(content=bot_reply))
    chat_sessions[session_id] = [
        {"type": "human", "content": msg.content} if isinstance(msg, HumanMessage) else {"type": "ai", "content": msg.content}
        for msg in formatted_history
    ]

    llm_prompt = f"""
    You are an expert text analyzer. Your task is to extract **movie**, **TV show**, **anime movie**, and **anime series** names along with their release years from the chatbot response.
    **Instructions:**
    - Identify and extract **movie titles**, including **anime movies**, if they exist.
    - Identify and extract **TV show titles**, including **anime series**, if they exist.
    - If a title has a **release year** mentioned in the response, extract that too.
    - If no year is mentioned, return null for that title.
    - If no movies, anime movies, TV shows, or anime series are found, return an empty list for both.
    - Return only **valid JSON output**, and **do NOT add any extra text or explanations**.
    **Example JSON Format:**
    {{
        "movies": [
            {{"title": "Inception", "year": 2010}},
            {{"title": "Titanic", "year": 1997}},
            {{"title": "Your Name", "year": 2016}}
        ],
        "tv_shows": [
            {{"title": "Breaking Bad", "year": 2008}},
            {{"title": "Friends", "year": 1994}},
            {{"title": "Attack on Titan", "year": 2013}}
        ]
    }}
    **Chatbot Response to Process:**
    "{bot_reply}"
    """
    analysis_response = chatbot.invoke(llm_prompt)
    try:
        analysis_data = json.loads(analysis_response.content)
        movie_data = analysis_data.get("movies", [])
        tv_show_data = analysis_data.get("tv_shows", [])
    except json.JSONDecodeError:
        print(f"Invalid JSON from analysis: {analysis_response.content}")
        movie_data = []
        tv_show_data = []

    if not movie_data and not tv_show_data:
        return jsonify({"reply": "I couldn't find this movie or TV show. Could you provide more details like the year, synopsis, or any actors?"})

    media_data = {"movies": [], "tv_shows": []}
    for media_list, media_type, key in [(movie_data, "movie", "movies"), (tv_show_data, "tv", "tv_shows")]:
        for media in media_list:
            title = media["title"]
            year = media["year"]
            url = f"https://api.themoviedb.org/3/search/{media_type}?api_key={TMDB_API_KEY}&query={title}&page=1&include_adult=true"
            if year:
                url += f"&year={year}"
            response = requests.get(url).json()
            results = response.get("results", [])
            if not results:
                print(f"⚠️ No {media_type} results found for: {title}")
                continue
            media_info = results[0]
            media_id = media_info.get("id")
            poster_path = media_info.get("poster_path")
            media_data[key].append({
                "title": media_info["title"] if media_type == "movie" else media_info["name"],
                "year": media_info.get("release_date", "Unknown")[:4] if media_type == "movie" else media_info.get("first_air_date", "Unknown")[:4],
                "poster_url": f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else "https://via.placeholder.com/500x750?text=No+Image",
                "tmdb_link": f"/{media_type}/{media_id}"
            })

    response_data = {"reply": bot_reply}
    if media_data["movies"]:
        response_data["movies"] = media_data["movies"]
    if media_data["tv_shows"]:
        response_data["tv_shows"] = media_data["tv_shows"]
    return jsonify(response_data)

def fetch_movie_details(movie_id, max_retries=3, retry_delay=2):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US&append_to_response=credits,videos,recommendations,reviews"
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            if 'success' in data and not data['success']:
                raise Exception(f"TMDb API error: {data.get('status_message', 'Unknown error')}")
            break
        except (requests.exceptions.RequestException, Exception) as e:
            print(f"Attempt {attempt + 1}/{max_retries} failed for movie {movie_id}: {e}")
            if attempt + 1 == max_retries:
                raise Exception(f"Failed to fetch movie details after {max_retries} retries: {e}")
            time.sleep(retry_delay)
    
    print(f"Movie {movie_id} credits: {data.get('credits', {}).get('cast', [])[:12]}")  # Debug cast data
    
    movie = {
        'id': data.get('id'),
        'title': data.get('title'),
        'overview': data.get('overview'),
        'tagline': data.get('tagline'),
        'release_date': data.get('release_date'),
        'runtime': format_runtime(data.get('runtime')),
        'vote_average': round(data.get('vote_average', 0), 1),
        'vote_count': data.get('vote_count', 0),
        'status': data.get('status'),
        'original_language': data.get('original_language'),
        'budget': format_currency(data.get('budget')),
        'revenue': format_currency(data.get('revenue')),
        'poster_path': f"https://image.tmdb.org/t/p/w500{data.get('poster_path')}" if data.get('poster_path') else "https://via.placeholder.com/500x750?text=No+Image",
        'backdrop_path': f"https://image.tmdb.org/t/p/original{data.get('backdrop_path')}" if data.get('backdrop_path') else "https://via.placeholder.com/1920x1080?text=No+Backdrop",
        'genres': [genre['name'] for genre in data.get('genres', [])],
        'trailer_url': None,
        'certification': None
    }
    
    # Fetch certification
    release_url = f"https://api.themoviedb.org/3/movie/{movie_id}/release_dates?api_key={TMDB_API_KEY}"
    release_response = requests.get(release_url)
    if release_response.status_code == 200:
        release_data = release_response.json()
        for result in release_data.get('results', []):
            if result.get('iso_3166_1') == 'US':
                for release in result.get('release_dates', []):
                    movie['certification'] = release.get('certification') or None
                    break
                break
    
    credits = data.get('credits', {})
    crew = credits.get('crew', [])
    for person in crew:
        if person.get('job') == 'Director':
            movie['director'] = person.get('name')
        elif person.get('job') in ['Screenplay', 'Writer']:
            movie['writer'] = person.get('name')
    
    movie['cast'] = [
        {
            'id': cast_member.get('id'),
            'name': cast_member.get('name'),
            'character': cast_member.get('character'),
            'profile_path': f"https://image.tmdb.org/t/p/w185{cast_member.get('profile_path')}" if cast_member.get('profile_path') else "https://via.placeholder.com/185x278?text=No+Image"
        } for cast_member in credits.get('cast', [])[:12]
    ]
    
    videos = data.get('videos', {}).get('results', [])
    for video in videos:
        if video.get('type') == 'Trailer' and video.get('site') == 'YouTube':
            movie['trailer_url'] = f"https://www.youtube.com/embed/{video.get('key')}"
            break
    
    movie['recommendations'] = [
        {
            'id': rec.get('id'),
            'title': rec.get('title'),
            'release_date': rec.get('release_date'),
            'poster_path': f"https://image.tmdb.org/t/p/w500{rec.get('poster_path')}" if rec.get('poster_path') else "https://via.placeholder.com/500x750?text=No+Image"
        } for rec in data.get('recommendations', {}).get('results', [])[:12]
    ]
    
    movie['reviews'] = [
        {
            'author': review.get('author'),
            'content': review.get('content'),
            'created_at': review.get('created_at'),
            'rating': round(review.get('author_details', {}).get('rating', 0) / 2) if review.get('author_details', {}).get('rating') is not None else 0,
            'author_avatar': f"https://www.gravatar.com/avatar/{hashlib.md5(review.get('author', '').lower().encode()).hexdigest()}?s=100&d=identicon"
        } for review in data.get('reviews', {}).get('results', [])[:4]
    ]
    
    return movie

def fetch_tv_show_details(show_id, max_retries=3, retry_delay=2):
    url = f"https://api.themoviedb.org/3/tv/{show_id}?api_key={TMDB_API_KEY}&language=en-US&append_to_response=credits,videos,recommendations,reviews,seasons"
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            if 'success' in data and not data['success']:
                raise Exception(f"TMDb API error: {data.get('status_message', 'Unknown error')}")
            break
        except (requests.exceptions.RequestException, Exception) as e:
            print(f"Attempt {attempt + 1}/{max_retries} failed for show {show_id}: {e}")
            if attempt + 1 == max_retries:
                raise Exception(f"Failed to fetch TV show details after {max_retries} retries: {e}")
            time.sleep(retry_delay)
    
    show = {
        'id': data.get('id'),
        'name': data.get('name'),
        'overview': data.get('overview'),
        'tagline': data.get('tagline'),
        'first_air_date': data.get('first_air_date'),
        'last_air_date': data.get('last_air_date'),
        'number_of_seasons': data.get('number_of_seasons'),
        'number_of_episodes': data.get('number_of_episodes'),
        'vote_average': round(data.get('vote_average', 0), 1),
        'vote_count': data.get('vote_count', 0),
        'status': data.get('status'),
        'original_language': data.get('original_language'),
        'poster_path': f"https://image.tmdb.org/t/p/w500{data.get('poster_path')}" if data.get('poster_path') else "https://via.placeholder.com/500x750?text=No+Image",
        'backdrop_path': f"https://image.tmdb.org/t/p/original{data.get('backdrop_path')}" if data.get('backdrop_path') else "https://via.placeholder.com/1920x1080?text=No+Backdrop",
        'genres': [genre['name'] for genre in data.get('genres', [])],
        'trailer_url': None
    }
    
    credits = data.get('credits', {})
    crew = credits.get('crew', [])
    for person in crew:
        if person.get('job') == 'Creator':
            show['creator'] = person.get('name')
            break
    
    show['cast'] = [
        {
            'id': cast_member.get('id'),
            'name': cast_member.get('name'),
            'character': cast_member.get('character'),
            'profile_path': f"https://image.tmdb.org/t/p/w185{cast_member.get('profile_path')}" if cast_member.get('profile_path') else "https://via.placeholder.com/185x278?text=No+Image"
        } for cast_member in credits.get('cast', [])[:12]
    ]
    
    show['seasons'] = [
        {
            'id': season.get('id'),
            'name': season.get('name'),
            'overview': season.get('overview'),
            'air_date': season.get('air_date'),
            'episode_count': season.get('episode_count'),
            'poster_path': f"https://image.tmdb.org/t/p/w500{season.get('poster_path')}" if season.get('poster_path') else "https://via.placeholder.com/500x750?text=No+Image"
        } for season in data.get('seasons', [])
    ]
    
    videos = data.get('videos', {}).get('results', [])
    for video in videos:
        if video.get('type') == 'Trailer' and video.get('site') == 'YouTube':
            show['trailer_url'] = f"https://www.youtube.com/embed/{video.get('key')}"
            break
    
    show['recommendations'] = [
        {
            'id': rec.get('id'),
            'name': rec.get('name'),
            'first_air_date': rec.get('first_air_date'),
            'poster_path': f"https://image.tmdb.org/t/p/w500{rec.get('poster_path')}" if rec.get('poster_path') else "https://via.placeholder.com/500x750?text=No+Image"
        } for rec in data.get('recommendations', {}).get('results', [])[:12]
    ]
    
    show['reviews'] = [
        {
            'author': review.get('author'),
            'content': review.get('content'),
            'created_at': review.get('created_at'),
            'rating': round(review.get('author_details', {}).get('rating', 0) / 2) if review.get('author_details', {}).get('rating') is not None else 0,
            'author_avatar': f"https://www.gravatar.com/avatar/{hashlib.md5(review.get('author', '').lower().encode()).hexdigest()}?s=100&d=identicon"
        } for review in data.get('reviews', {}).get('results', [])[:4]
    ]
    
    return show

def fetch_actor_details(actor_id, max_retries=3, retry_delay=2):
    # Fetch actor details
    url = f"https://api.themoviedb.org/3/person/{actor_id}?api_key={TMDB_API_KEY}&language=en-US"
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            if 'success' in data and not data['success']:
                raise Exception(f"TMDb API error: {data.get('status_message', 'Unknown error')}")
            break
        except (requests.exceptions.RequestException, Exception) as e:
            print(f"Attempt {attempt + 1}/{max_retries} failed for actor {actor_id}: {e}")
            if attempt + 1 == max_retries:
                raise Exception(f"Failed to fetch actor details after {max_retries} retries: {e}")
            time.sleep(retry_delay)
    
    print(f"Actor {actor_id} data: {data}")  # Debug actor data
    actor_data = data

    # Fetch movie credits
    movie_credits_url = f"https://api.themoviedb.org/3/person/{actor_id}/movie_credits?api_key={TMDB_API_KEY}&language=en-US"
    for attempt in range(max_retries):
        try:
            movie_response = requests.get(movie_credits_url, timeout=5)
            movie_response.raise_for_status()
            movie_credits_data = movie_response.json()
            break
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1}/{max_retries} failed for movie credits of actor {actor_id}: {e}")
            if attempt + 1 == max_retries:
                raise Exception(f"Failed to fetch movie credits after {max_retries} retries: {e}")
            time.sleep(retry_delay)

    # Fetch TV credits
    tv_credits_url = f"https://api.themoviedb.org/3/person/{actor_id}/tv_credits?api_key={TMDB_API_KEY}&language=en-US"
    for attempt in range(max_retries):
        try:
            tv_response = requests.get(tv_credits_url, timeout=5)
            tv_response.raise_for_status()
            tv_credits_data = tv_response.json()
            break
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1}/{max_retries} failed for TV credits of actor {actor_id}: {e}")
            if attempt + 1 == max_retries:
                raise Exception(f"Failed to fetch TV credits after {max_retries} retries: {e}")
            time.sleep(retry_delay)

    # Fetch tagged images (deprecated but still functional)
    tagged_images = []
    try:
        tagged_images_url = f"https://api.themoviedb.org/3/person/{actor_id}/tagged_images?api_key={TMDB_API_KEY}"
        tagged_response = requests.get(tagged_images_url)
        if tagged_response.status_code == 200 and ('success' not in tagged_response.json() or tagged_response.json()['success']):
            tagged_data = tagged_response.json()
            seen_file_paths = set()
            tagged_images = []
            for img in sorted(tagged_data.get('results', []), key=lambda x: x.get('vote_average', 0), reverse=True):
                if img.get('file_path') and img['file_path'] not in seen_file_paths:
                    seen_file_paths.add(img['file_path'])
                    img['file_path'] = f"https://image.tmdb.org/t/p/w500{img['file_path']}"
                    tagged_images.append(img)
    except Exception as e:
        print(f"Failed to fetch tagged images for actor {actor_id}: {e}")

    # Fetch external IDs (with fallback)
    external_ids = {
        'facebook_id': None,
        'instagram_id': None,
        'tiktok_id': None,
        'twitter_id': None,
        'youtube_id': None,
        'imdb_id': None,
        'wikidata_id': None,
        'freebase_mid': None,
        'freebase_id': None,
        'tvrage_id': 0,
    }
    try:
        external_ids_url = f"https://api.themoviedb.org/3/person/{actor_id}/external_ids?api_key={TMDB_API_KEY}"
        external_response = requests.get(external_ids_url)
        if external_response.status_code == 200 and ('success' not in external_response.json() or external_response.json()['success']):
            external_ids_data = external_response.json()
            external_ids.update({
                'facebook_id': external_ids_data.get('facebook_id', None),
                'instagram_id': external_ids_data.get('instagram_id', None),
                'tiktok_id': external_ids_data.get('tiktok_id', None),
                'twitter_id': external_ids_data.get('twitter_id', None),
                'youtube_id': external_ids_data.get('youtube_id', None),
                'imdb_id': external_ids_data.get('imdb_id', None),
                'wikidata_id': external_ids_data.get('wikidata_id', None),
                'freebase_mid': external_ids_data.get('freebase_mid', None),
                'freebase_id': external_ids_data.get('freebase_id', None),
                'tvrage_id': external_ids_data.get('tvrage_id', 0),
            })
    except Exception as e:
        print(f"Failed to fetch external IDs for actor {actor_id}: {e}")

    # Fetch profile images (with fallback)
    profile_images = []
    try:
        images_url = f"https://api.themoviedb.org/3/person/{actor_id}/images?api_key={TMDB_API_KEY}"
        images_response = requests.get(images_url)
        if images_response.status_code == 200 and ('success' not in images_response.json() or images_response.json()['success']):
            images_data = images_response.json()
            profile_images = sorted(
                images_data.get('profiles', []),
                key=lambda x: x.get('vote_average', 0),
                reverse=True
            )
            for img in profile_images:
                img['file_path'] = f"https://image.tmdb.org/t/p/w500{img['file_path']}" if img.get('file_path') else "https://via.placeholder.com/500x750?text=No+Image"
    except Exception as e:
        print(f"Failed to fetch profile images for actor {actor_id}: {e}")

    # Process movie credits, removing duplicates by id
    movie_acting_credits = []
    seen_movie_ids = set()
    for credit in sorted(movie_credits_data.get('cast', []), key=lambda x: x.get('popularity', 0), reverse=True):
        if credit.get('id') not in seen_movie_ids and credit.get('release_date', '9999-12-31') <= '2025-04-08':
            seen_movie_ids.add(credit['id'])
            movie_acting_credits.append(credit)

    movie_production_credits = []
    seen_movie_prod_ids = set()
    for credit in sorted(movie_credits_data.get('crew', []), key=lambda x: x.get('popularity', 0), reverse=True):
        if credit.get('id') not in seen_movie_prod_ids:
            seen_movie_prod_ids.add(credit['id'])
            movie_production_credits.append(credit)

    # Process TV credits, removing duplicates by id
    tv_acting_credits = []
    seen_tv_ids = set()
    for credit in sorted(tv_credits_data.get('cast', []), key=lambda x: x.get('popularity', 0), reverse=True):
        if credit.get('id') not in seen_tv_ids and credit.get('first_air_date', '9999-12-31') <= '2025-04-08':
            seen_tv_ids.add(credit['id'])
            tv_acting_credits.append(credit)

    tv_production_credits = []
    seen_tv_prod_ids = set()
    for credit in sorted(tv_credits_data.get('crew', []), key=lambda x: x.get('popularity', 0), reverse=True):
        if credit.get('id') not in seen_tv_prod_ids:
            seen_tv_prod_ids.add(credit['id'])
            tv_production_credits.append(credit)

    # Use full lists for known_for, already deduplicated
    known_for_movies = movie_acting_credits
    known_for_tv = tv_acting_credits

    # Construct actor dictionary
    actor = {
        'name': actor_data.get('name', 'Unknown Actor'),
        'biography': actor_data.get('biography', 'No biography available.'),
        'birth_date': actor_data.get('birthday', 'N/A'),
        'place_of_birth': actor_data.get('place_of_birth', 'Unknown'),
        'gender': 'Female' if actor_data.get('gender') == 1 else 'Male' if actor_data.get('gender') == 2 else 'Unknown',
        'known_for_department': actor_data.get('known_for_department', 'N/A'),
        'known_credits': len(movie_acting_credits) + len(tv_acting_credits),
        'known_for_movies': known_for_movies,
        'known_for_tv': known_for_tv,
        'movie_acting_credits': movie_acting_credits,
        'tv_acting_credits': tv_acting_credits,
        'movie_production_credits': movie_production_credits,
        'tv_production_credits': tv_production_credits,
        'tagged_images': tagged_images,
        'profile_path': f"https://image.tmdb.org/t/p/w500{actor_data.get('profile_path')}" if actor_data.get('profile_path') else "https://via.placeholder.com/500x750?text=No+Image",
        'backdrop_path': f"https://image.tmdb.org/t/p/original{actor_data.get('profile_path')}" if actor_data.get('profile_path') else "https://via.placeholder.com/1920x1080?text=No+Backdrop",
        'also_known_as': actor_data.get('also_known_as', []),
        'popularity': actor_data.get('popularity', 0.0),
        'imdb_id': actor_data.get('imdb_id', None),
        'external_ids': external_ids,
        'profile_images': profile_images
    }

    return actor

def format_runtime(minutes):
    if not minutes:
        return "N/A"
    hours = minutes // 60
    remaining_minutes = minutes % 60
    return f"{hours}h {remaining_minutes}m" if hours > 0 else f"{remaining_minutes}m"

def format_currency(amount):
    if not amount:
        return "N/A"
    return f"{amount:,}"

@app.route('/movie/<int:movie_id>')
def movie_detail(movie_id):
    try:
        movie = fetch_movie_details(movie_id)
        return render_template('movie_detail.html', movie=movie)
    except Exception as e:
        print(f"Error fetching movie details: {e}")
        return render_template('error.html', message="Could not fetch movie details. Please try again later.")

@app.route('/tv/<int:show_id>')
def tv_detail(show_id):
    try:
        show = fetch_tv_show_details(show_id)
        return render_template('tv_detail.html', show=show)
    except Exception as e:
        print(f"Error fetching TV show details: {e}")
        return render_template('error.html', message="Could not fetch TV show details. Please try again later.")

@app.route('/actor/<int:actor_id>')
def actor_detail(actor_id):
    try:
        actor = fetch_actor_details(actor_id)
        return render_template('actor_detail.html', actor=actor)
    except Exception as e:
        print(f"Error fetching actor details: {e}")
        return render_template('error.html', message="Could not fetch actor details. Please try again later.")

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)