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

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_API_KEY_2 = os.getenv("TMDB_API_KEY_2")
GROQ_API_KEY = os.getenv("groq_api_key")


chatbot = ChatGroq(model_name="llama3-70b-8192", api_key=GROQ_API_KEY)


prompt_template = PromptTemplate(
    input_variables=["chat_history", "user_input"],
    template="You are a helpful movie recommendation assistant. Here is the conversation so far:\n{chat_history}\nUser: {user_input}\nAssistant:"
)

# Updated conversation chain using new LangChain method
conversation_chain = prompt_template | chatbot

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
    return render_template('index.html', api_key=TMDB_API_KEY_2)

@app.route('/tv_shows')
def tv_shows():
    return render_template('tv_shows.html', api_key=TMDB_API_KEY_2)

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

def fetch_poster(id, is_movie=True, max_retries=3, retry_delay=2):
    media_type = "movie" if is_movie else "tv"
    url = f"https://api.themoviedb.org/3/{media_type}/{id}?api_key={TMDB_API_KEY}&language=en-US"

    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            poster_path = data.get('poster_path')
            if poster_path:
                return f"https://image.tmdb.org/t/p/w500/{poster_path}"
            return None  # No poster found
        
        except requests.exceptions.Timeout:
            print(f"Timeout error on attempt {attempt + 1}/{max_retries}. Retrying in {retry_delay}s...")
        
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
            break  # No need to retry for 4xx or 5xx errors
        
        except requests.exceptions.RequestException as req_err:
            print(f"Request error: {req_err}. Retrying in {retry_delay}s...")

        time.sleep(retry_delay)

    print("Failed to fetch poster after multiple retries.")
    return None  # Return None if all retries fail

def fetch_tmdb_recommendations(id, is_movie=True, max_recommendations=50):
    media_type = "movie" if is_movie else "tv"
    url = f"https://api.themoviedb.org/3/{media_type}/{id}/recommendations?api_key={TMDB_API_KEY}&language=en-US&page=1"
    time.sleep(1)
    response = requests.get(url)
    data = response.json()
    recommendations = data.get('results', [])
    return recommendations[:max_recommendations]

@app.route("/chat")  
def chat():
    return render_template("chat.html")  # Ensure chat.html exists in 'templates/'


chat_sessions = {}

@app.route("/chat_api", methods=["POST"])
def chat_api():
    user_message = request.json.get("message")
    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    session_id = request.remote_addr  # Using IP as a session identifier

    # Preserve chat history instead of resetting on each request
    if session_id not in chat_sessions:
        chat_sessions[session_id] = []

    formatted_history = [
        HumanMessage(content=msg["content"]) if msg["type"] == "human"
        else AIMessage(content=msg["content"])
        for msg in chat_sessions[session_id]
    ]

    formatted_history.append(HumanMessage(content=user_message))

    # **🔵 Get Bot Response**
    bot_response = conversation_chain.invoke({"chat_history": formatted_history, "user_input": user_message})
    bot_reply = bot_response.content.strip()

    if not bot_reply:
        return jsonify({"error": "Bot response is empty. Please try again."}), 500

    formatted_history.append(AIMessage(content=bot_reply))
    chat_sessions[session_id] = [
        {"type": "human", "content": msg.content} if isinstance(msg, HumanMessage)
        else {"type": "ai", "content": msg.content}
        for msg in formatted_history
    ]

    # **🔵 LLM Prompt to Extract Movie & TV Show Names with Year**
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

    Extract and return **ONLY** the JSON.
    """

    # 🔵 Invoke LLM to extract movie & TV show names along with the release year
    analysis_response = chatbot.invoke(llm_prompt)
    try:
        analysis_data = json.loads(analysis_response.content)
        movie_data = analysis_data.get("movies", [])
        tv_show_data = analysis_data.get("tv_shows", [])
    except json.JSONDecodeError:
        return jsonify({"reply": bot_reply, "error": "Invalid JSON format from analysis."})

    # **🔵 If LLM Fails to Recognize the Movie/TV Show, Ask for More Context**
    if not movie_data and not tv_show_data:
        return jsonify({
            "reply": "I couldn't find this movie or TV show. Could you provide more details like the year, synopsis, or any actors?"
        })

    media_data = {"movies": [], "tv_shows": []}

    # **🔵 Fetch Movie & TV Show Details from TMDB**
    for media_list, media_type, key in [(movie_data, "movie", "movies"), (tv_show_data, "tv", "tv_shows")]:
        for media in media_list:
            title = media["title"]
            year = media["year"]

            # 🔹 Construct TMDB search request
            url = f"https://api.themoviedb.org/3/search/{media_type}?api_key={TMDB_API_KEY}&query={title}&page=1&include_adult=true"
            if year:  # Add year filter if available
                url += f"&year={year}"

            response = requests.get(url).json()
            results = response.get("results", [])

            if not results:
                print(f"⚠️ No {media_type} results found for:", title)
                continue  # Skip to next item

            media_info = results[0]  # Taking the first search result
            media_id = media_info.get("id")
            poster_path = media_info.get("poster_path")

            media_data[key].append({
                "title": media_info["title"] if media_type == "movie" else media_info["name"],
                "year": media_info.get("release_date", "Unknown")[:4] if media_type == "movie" else media_info.get("first_air_date", "Unknown")[:4],
                "poster_url": f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else "https://via.placeholder.com/500x750?text=No+Image",
                "tmdb_link": f"/{media_type}/{media_id}"
            })

    # **🔵 Prepare JSON Response**
    response_data = {"reply": bot_reply}
    if media_data["movies"]:
        response_data["movies"] = media_data["movies"]
    if media_data["tv_shows"]:
        response_data["tv_shows"] = media_data["tv_shows"]

    return jsonify(response_data)

def fetch_movie_details(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US&append_to_response=credits,videos,recommendations,reviews"
    response = requests.get(url)
    data = response.json()
    
    # Extract basic movie information
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
        'poster_path': f"https://image.tmdb.org/t/p/w500{data.get('poster_path')}" if data.get('poster_path') else None,
        'backdrop_path': f"https://image.tmdb.org/t/p/original{data.get('backdrop_path')}" if data.get('backdrop_path') else None,
        'genres': [genre['name'] for genre in data.get('genres', [])],
        'trailer_url': None
    }
    
    # Extract director and writer
    credits = data.get('credits', {})
    crew = credits.get('crew', [])
    
    for person in crew:
        if person.get('job') == 'Director':
            movie['director'] = person.get('name')
        elif person.get('job') == 'Screenplay' or person.get('job') == 'Writer':
            movie['writer'] = person.get('name')
    
    # Extract cast
    movie['cast'] = []
    for cast_member in credits.get('cast', [])[:12]:
        movie['cast'].append({
            'id': cast_member.get('id'),
            'name': cast_member.get('name'),
            'character': cast_member.get('character'),
            'profile_path': f"https://image.tmdb.org/t/p/w185{cast_member.get('profile_path')}" if cast_member.get('profile_path') else None
        })
    
    # Extract trailer
    videos = data.get('videos', {}).get('results', [])
    for video in videos:
        if video.get('type') == 'Trailer' and video.get('site') == 'YouTube':
            movie['trailer_url'] = f"https://www.youtube.com/embed/{video.get('key')}"
            break
    
    # Extract recommendations
    movie['recommendations'] = []
    for rec in data.get('recommendations', {}).get('results', [])[:12]:
        movie['recommendations'].append({
            'id': rec.get('id'),
            'title': rec.get('title'),
            'release_date': rec.get('release_date'),
            'poster_path': f"https://image.tmdb.org/t/p/w500{rec.get('poster_path')}" if rec.get('poster_path') else None
        })
    
    # Extract reviews
    movie['reviews'] = []
    for review in data.get('reviews', {}).get('results', [])[:4]:
        movie['reviews'].append({
            'author': review.get('author'),
            'content': review.get('content'),
            'created_at': review.get('created_at'),
            'rating': round(review.get('author_details', {}).get('rating', 0) / 2),  # Convert 10-point scale to 5-point
            'author_avatar': f"https://www.gravatar.com/avatar/{hash(review.get('author', '').lower())}?s=100&d=identicon"
        })
    
    return movie

def fetch_tv_show_details(show_id):
    url = f"https://api.themoviedb.org/3/tv/{show_id}?api_key={TMDB_API_KEY}&language=en-US&append_to_response=credits,videos,recommendations,reviews,seasons"
    response = requests.get(url)
    data = response.json()
    
    # Extract basic show information
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
        'poster_path': f"https://image.tmdb.org/t/p/w500{data.get('poster_path')}" if data.get('poster_path') else None,
        'backdrop_path': f"https://image.tmdb.org/t/p/original{data.get('backdrop_path')}" if data.get('backdrop_path') else None,
        'genres': [genre['name'] for genre in data.get('genres', [])],
        'trailer_url': None
    }
    
    # Extract creator
    credits = data.get('credits', {})
    crew = credits.get('crew', [])
    
    for person in crew:
        if person.get('job') == 'Creator':
            show['creator'] = person.get('name')
            break
    
    # Extract cast
    show['cast'] = []
    for cast_member in credits.get('cast', [])[:12]:
        show['cast'].append({
            'id': cast_member.get('id'),
            'name': cast_member.get('name'),
            'character': cast_member.get('character'),
            'profile_path': f"https://image.tmdb.org/t/p/w185{cast_member.get('profile_path')}" if cast_member.get('profile_path') else None
        })
    
    # Extract seasons
    show['seasons'] = []
    for season in data.get('seasons', []):
        show['seasons'].append({
            'id': season.get('id'),
            'name': season.get('name'),
            'overview': season.get('overview'),
            'air_date': season.get('air_date'),
            'episode_count': season.get('episode_count'),
            'poster_path': f"https://image.tmdb.org/t/p/w500{season.get('poster_path')}" if season.get('poster_path') else None
        })
    
    # Extract trailer
    videos = data.get('videos', {}).get('results', [])
    for video in videos:
        if video.get('type') == 'Trailer' and video.get('site') == 'YouTube':
            show['trailer_url'] = f"https://www.youtube.com/embed/{video.get('key')}"
            break
    
    # Extract recommendations
    show['recommendations'] = []
    for rec in data.get('recommendations', {}).get('results', [])[:12]:
        show['recommendations'].append({
            'id': rec.get('id'),
            'name': rec.get('name'),
            'first_air_date': rec.get('first_air_date'),
            'poster_path': f"https://image.tmdb.org/t/p/w500{rec.get('poster_path')}" if rec.get('poster_path') else None
        })
    
    # Extract reviews
    show['reviews'] = []
    for review in data.get('reviews', {}).get('results', [])[:4]:
        show['reviews'].append({
            'author': review.get('author'),
            'content': review.get('content'),
            'created_at': review.get('created_at'),
            'rating': round(review.get('author_details', {}).get('rating', 0) / 2),  # Convert 10-point scale to 5-point
            'author_avatar': f"https://www.gravatar.com/avatar/{hash(review.get('author', '').lower())}?s=100&d=identicon"
        })
    
    return show

def format_runtime(minutes):
    if not minutes:
        return "N/A"
    hours = minutes // 60
    remaining_minutes = minutes % 60
    if hours > 0:
        return f"{hours}h {remaining_minutes}m"
    return f"{remaining_minutes}m"

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

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)