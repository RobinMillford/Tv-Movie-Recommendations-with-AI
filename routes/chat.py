from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
import requests
import os
from api.chatbot import get_chatbot, clean_json_response, is_recent_release, is_upcoming_release, is_safety_model_response, extract_media_with_llm
from langchain.schema import AIMessage, HumanMessage
import json
from datetime import datetime
import re

# Get environment variables
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

chat = Blueprint('chat', __name__)

# In-memory session storage
chat_sessions = {}

@chat.route("/model_selection")
def model_selection():
    """Route to display the model selection page"""
    # Check if user is authenticated
    if current_user.is_authenticated:
        return render_template("model_selection.html")
    else:
        return render_template("model_selection_login_required.html")

@chat.route("/chat")
@login_required
def chat_page():
    # Get the model name from the query parameter, or use default
    model_name = request.args.get("model", "llama-3.3-70b-versatile")
    
    # Clear session history for this user on page load
    session_id = request.remote_addr
    if session_id in chat_sessions:
        del chat_sessions[session_id]
        
    return render_template("chat.html", model=model_name)

@chat.route("/chat_api", methods=["POST"])
@login_required
def chat_api():
    user_message = request.json.get("message")
    model_name = request.json.get("model", "llama-3.3-70b-versatile")
    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    session_id = request.remote_addr
    if session_id not in chat_sessions:
        chat_sessions[session_id] = []

    # Use the chatbot for the specified model
    current_chatbot = get_chatbot(model_name)
    
    # Check if awaiting clarification
    is_awaiting_clarification = any(
        msg.get("type") == "ai" and "please provide the movie's true name and release year" in msg.get("content", "").lower()
        for msg in chat_sessions[session_id][-1:]
    )

    formatted_history = [
        HumanMessage(content=msg["content"]) if msg["type"] == "human" else AIMessage(content=msg["content"])
        for msg in chat_sessions[session_id]
    ]
    formatted_history.append(HumanMessage(content=user_message))

    if is_awaiting_clarification:
        # Expect movie name and year
        try:
            parts = user_message.replace(',', '').split()
            if len(parts) < 2 or not parts[-1].isdigit():
                return jsonify({"reply": "Please provide the movie name and year, e.g., 'Dune, 2025' or 'Dune 2025'."})

            year = parts[-1]
            title = ' '.join(parts[:-1])
            # Search TMDb with more flexible approach for new releases
            search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={title}&include_adult=true"
            search_response = requests.get(search_url).json()
            results = search_response.get("results", [])

            # Filter results by year if provided
            if year and results:
                results = [movie for movie in results if movie.get('release_date', '').startswith(year)]
            
            # If no results found with exact year match, try broader search
            if not results:
                # Try without year constraint but with include_video=true for newer releases
                search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={title}&include_adult=true&include_video=true"
                search_response = requests.get(search_url).json()
                results = search_response.get("results", [])
                
                # Filter by year again if provided
                if year and results:
                    results = [movie for movie in results if movie.get('release_date', '').startswith(year)]

            if not results:
                bot_reply = f"No movies found for '{title}' in {year}. Could you clarify the title or try another year?"
                formatted_history.append(AIMessage(content=bot_reply))
                chat_sessions[session_id] = [
                    {"type": "human", "content": msg.content} if isinstance(msg, HumanMessage)
                    else {"type": "ai", "content": msg.content}
                    for msg in formatted_history
                ]
                return jsonify({"reply": bot_reply})

            movie = results[0]
            movie_id = movie['id']
            # Fetch full movie details
            details_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&append_to_response=credits,release_dates"
            details_response = requests.get(details_url).json()
            if not details_response or 'status_code' in details_response:
                print(f"TMDb error: {details_response.get('status_message', 'Unknown error')}")
                bot_reply = "Sorry, I couldn't retrieve details for this movie. Please try again later."
                formatted_history.append(AIMessage(content=bot_reply))
                chat_sessions[session_id] = [
                    {"type": "human", "content": msg.content} if isinstance(msg, HumanMessage)
                    else {"type": "ai", "content": msg.content}
                    for msg in formatted_history
                ]
                return jsonify({"reply": bot_reply})

            # Extract details with robust error handling
            title = details_response.get('title', 'Unknown')
            release_date = details_response.get('release_date', 'Unknown')
            release_year = release_date[:4] if release_date != 'Unknown' else 'Unknown'
            overview = details_response.get('overview', 'No description available')
            genres = [genre['name'] for genre in details_response.get('genres', [])] or ['Unknown']
            cast = [
                {'name': member['name'], 'character': member['character']}
                for member in details_response.get('credits', {}).get('cast', [])[:5]
            ] or [{'name': 'Unknown', 'character': 'Unknown'}]
            director = next(
                (member['name'] for member in details_response.get('credits', {}).get('crew', []) 
                 if member['job'] == 'Director'), 'Unknown'
            )
            production_companies = [
                company['name'] for company in details_response.get('production_companies', [])
            ] or ['Unknown']
            poster_path = details_response.get('poster_path')
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else "https://via.placeholder.com/500x750?text=No+Image"
            runtime = details_response.get('runtime', 0)
            runtime_str = f"{runtime // 60}h {runtime % 60}m" if runtime else "Unknown"
            # Safely handle rating
            release_dates = details_response.get('release_dates', {}).get('results', [])
            us_release = next((release for release in release_dates if release['iso_3166_1'] == 'US'), None)
            rating = 'NR'
            if us_release and us_release.get('release_dates'):
                for release in us_release['release_dates']:
                    if release.get('certification'):
                        rating = release['certification']
                        break

            # Check if this is a recent or upcoming release
            is_recent = is_recent_release(release_date)
            is_upcoming = is_upcoming_release(release_date)
            release_status = ""
            if is_upcoming:
                release_status = " (UPCOMING RELEASE)"
            elif is_recent:
                release_status = " (RECENT RELEASE)"

            # Store movie data
            movie_data = [{
                "title": title,
                "year": release_year,
                "poster_url": poster_url,
                "tmdb_link": f"/movie/{movie_id}",
                "overview": overview,
                "genres": genres,
                "cast": cast,
                "director": director,
                "production_companies": production_companies,
                "runtime": runtime_str,
                "rating": rating
            }]

            # Generate recommendations with deep overview analysis
            recommendation_prompt = f"""
            You are an expert movie recommendation system. Carefully analyze the movie's overview to identify key themes (e.g., secrets, deception, technology, isolation), settings (e.g., secluded estate, cabin), and character dynamics (e.g., friendships, betrayal). Use these insights, along with genres, cast, director, and other details, to suggest up to 5 movies that closely match in themes, atmosphere, or narrative style. For each suggestion, provide the title, release year, and a brief reason explaining how it connects to the overview's themes or other details. Return valid JSON with a 'recommendations' key containing a list of objects with 'title', 'year', and 'reason' keys. Do NOT add extra text or explanations.

            **Movie Details:**
            - Title: {title}
            - Year: {release_year}{release_status}
            - Genres: {', '.join(genres)}
            - Director: {director}
            - Cast: {', '.join(member['name'] for member in cast)}
            - Production Companies: {', '.join(production_companies)}
            - Overview: {overview}
            - Runtime: {runtime_str}
            - Rating: {rating}

            **Example JSON Format:**
            {{
                "recommendations": [
                    {{"title": "Ex Machina", "year": 2014, "reason": "Explores deception and advanced AI technology, mirroring the unsettling tech-driven secrets in the overview"}},
                    {{"title": "The Cabin in the Woods", "year": 2012, "reason": "Shares a secluded setting with a group of friends facing unexpected horrors, like the lakeside estate scenario"}}
                ]
            }}
            """
            rec_response = get_chatbot(model_name).invoke(recommendation_prompt)
            try:
                rec_data = json.loads(rec_response.content)
                recommendations = rec_data.get("recommendations", [])
            except json.JSONDecodeError:
                print(f"Invalid JSON from recommendations: {rec_response.content}")
                recommendations = []

            bot_reply = (
                f"Found '{title}' ({release_year}){release_status}.\n"
                f"Overview: {overview}\n"
                f"Genres: {', '.join(genres)}\n"
                f"Director: {director}\n"
                f"Cast: {', '.join(member['name'] for member in cast)}\n"
                f"Production Companies: {', '.join(production_companies)}\n"
                f"Runtime: {runtime_str}\n"
                f"Rating: {rating}\n"
                f"Here are some similar movies you might enjoy:"
            )
            if recommendations:
                bot_reply += "\n" + "\n".join(
                    f"- {rec['title']} ({rec['year']}): {rec['reason']}"
                    for rec in recommendations
                )
            else:
                bot_reply += "\nNo similar movies found, but you might enjoy other sci-fi or thriller films!"

            formatted_history.append(AIMessage(content=bot_reply))
            chat_sessions[session_id] = [
                {"type": "human", "content": msg.content} if isinstance(msg, HumanMessage)
                else {"type": "ai", "content": msg.content}
                for msg in formatted_history
            ]
            response_data = {"reply": bot_reply, "movies": movie_data}
            if recommendations:
                response_data["recommendations"] = recommendations
            return jsonify(response_data)

        except Exception as e:
            print(f"Error processing clarification: {e}")
            bot_reply = "Something went wrong while fetching movie details. Please provide the movie name and year again."
            formatted_history.append(AIMessage(content=bot_reply))
            chat_sessions[session_id] = [
                {"type": "human", "content": msg.content} if isinstance(msg, HumanMessage)
                else {"type": "ai", "content": msg.content}
                for msg in formatted_history
            ]
            return jsonify({"reply": bot_reply})

    # Normal chat flow with enhanced media detection for new releases
    chat_history_str = "\n".join(
        f"{'User' if isinstance(msg, HumanMessage) else 'Assistant'}: {msg.content}"
        for msg in formatted_history[:-1]
    )
    
    # Enhanced prompt to better handle new releases and different media types
    enhanced_prompt = f"""
    You are a helpful movie and TV show recommendation assistant. You have access to The Movie Database (TMDB) which contains information about movies, TV shows, and anime including recent and upcoming releases.
    
    When users ask about movies or shows, especially recent ones, respond with accurate information. For newer releases that might not be widely known, provide details based on the information you have and mention that it's a recent release.
    
    Conversation so far:
    {chat_history_str}
    
    User: {user_message}
    
    Assistant:
    """
    
    bot_response = get_chatbot(model_name).invoke(enhanced_prompt)
    bot_reply = bot_response.content.strip()

    if not bot_reply:
        return jsonify({"error": "Bot response is empty. Please try again."}), 500

    # Special handling for the safety-focused model (Llama Guard)
    if is_safety_model_response(bot_reply, model_name):
        # Fallback to a more capable model for complex queries
        fallback_model = "llama-3.3-70b-versatile"
        bot_response = get_chatbot(fallback_model).invoke(enhanced_prompt)
        bot_reply = bot_response.content.strip()
        print(f"Fallback to {fallback_model} due to safety model response")
        # Update model_name for subsequent operations
        model_name = fallback_model

    # Check for uncertainty with improved detection for new releases
    uncertainty_prompt = f"""
    You are an expert text analyzer. Your task is to determine if the chatbot response indicates uncertainty or confusion about a movie or TV show.
    **Instructions:**
    - Look for phrases like "I'm not sure," "maybe," "guessing," "I don't know," "could be," or lack of specific movie details.
    - However, if the response is about a very recent or upcoming release, don't flag it as uncertain just because the LLM has limited knowledge about it.
    - Return valid JSON with a single key "is_uncertain" set to true or false.
    **Example JSON Format:**
    {{"is_uncertain": true}}
    **Chatbot Response to Analyze:**
    "{bot_reply}"
    """
    uncertainty_response = get_chatbot(model_name).invoke(uncertainty_prompt)
    try:
        uncertainty_data = json.loads(uncertainty_response.content)
        is_uncertain = uncertainty_data.get("is_uncertain", False)
    except json.JSONDecodeError:
        print(f"Invalid JSON from uncertainty analysis: {uncertainty_response.content}")
        # If we can't parse the JSON, check if it's the safety model response
        if is_safety_model_response(uncertainty_response.content, model_name):
            is_uncertain = False
        else:
            is_uncertain = False

    # Only ask for clarification if we're truly uncertain (not just about new releases)
    if is_uncertain and "2025" not in user_message and "recent" not in user_message.lower():
        bot_reply = (
            "I'm not confident about that movie or TV show. Could you please provide the title and year "
            "(e.g., 'Dune, 2025' or 'Dune 2025')?"
        )
        formatted_history.append(AIMessage(content=bot_reply))
        chat_sessions[session_id] = [
            {"type": "human", "content": msg.content} if isinstance(msg, HumanMessage)
            else {"type": "ai", "content": msg.content}
            for msg in formatted_history
        ]
        return jsonify({"reply": bot_reply})

    # Analysis for movies and TV shows with improved handling for new releases
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
            {{"title": "Your Name", "year": 2016}}
        ],
        "tv_shows": [
            {{"title": "Breaking Bad", "year": 2008}},
            {{"title": "Attack on Titan", "year": 2013}}
        ]
    }}
    **Chatbot Response to Process:**
    "{bot_reply}"
    """
    analysis_response = get_chatbot(model_name).invoke(llm_prompt)
    try:
        # Clean the JSON response by removing any markdown code block syntax
        cleaned_content = clean_json_response(analysis_response.content)
        analysis_data = json.loads(cleaned_content)
        movie_data = analysis_data.get("movies", [])
        tv_show_data = analysis_data.get("tv_shows", [])
    except json.JSONDecodeError:
        print(f"Invalid JSON from analysis: {analysis_response.content}")
        # Special handling for the safety model
        if is_safety_model_response(analysis_response.content, model_name):
            movie_data = []
            tv_show_data = []
        else:
            # Fallback to LLM-based extraction as a more robust approach
            movie_data, tv_show_data = extract_media_with_llm(bot_reply, model_name)

    # If we still don't have media data but the response mentions specific titles, try to extract them
    if not movie_data and not tv_show_data:
        # Use the improved title extraction function
        from api.chatbot import extract_media_titles, identify_media_type
        
        # Extract potential titles from the bot reply
        potential_titles = extract_media_titles(bot_reply)
        
        # Try to find years associated with titles
        year_matches = re.findall(r'\b(19|20)\d{2}\b', bot_reply)
        
        # Create movie data from potential titles
        for i, title in enumerate(potential_titles[:10]):  # Increase limit to 10 potential titles
            # Try to extract year from the title itself first
            year_match = re.search(r'\b(19|20)\d{2}\b', title)
            year = int(year_match.group()) if year_match else None
            
            # If no year in title, use year from year_matches
            if not year and i < len(year_matches):
                year = int(year_matches[i])
                
            # Clean up special titles
            clean_title = title.strip()
            # Handle special cases using the helper function
            from api.chatbot import _clean_special_titles
            clean_title = _clean_special_titles(clean_title)
            
            # Identify media type
            media_type = identify_media_type(clean_title)
            
            # Add to appropriate list
            if media_type in ['movie', 'anime']:
                movie_data.append({"title": clean_title, "year": year})
            else:
                tv_show_data.append({"title": clean_title, "year": year})

    # Additional fallback: If we still don't have data, try a more direct extraction
    if not movie_data and not tv_show_data:
        # Try to extract any movie/TV show-like patterns directly from the response
        from api.chatbot import extract_media_titles
        direct_titles = extract_media_titles(bot_reply)
        
        # For each title, try to search TMDB to see if it exists
        for title in direct_titles[:5]:  # Limit to first 5
            # Clean the title
            from api.chatbot import _clean_special_titles
            clean_title = _clean_special_titles(title)
            
            # Try to find year in the vicinity of the title
            # Look for a pattern like "Title (Year)" or "Title Year"
            title_with_context_pattern = rf'{re.escape(clean_title)}[^\d]{{0,20}}(\b(19|20)\d{{2}}\b)'
            context_match = re.search(title_with_context_pattern, bot_reply)
            year = int(context_match.group(1)) if context_match else None
            
            # Add to movie data by default, will be validated during TMDB search
            movie_data.append({"title": clean_title, "year": year})

    if not movie_data and not tv_show_data:
        formatted_history.append(AIMessage(content=bot_reply))
        chat_sessions[session_id] = [
            {"type": "human", "content": msg.content} if isinstance(msg, HumanMessage)
            else {"type": "ai", "content": msg.content}
            for msg in formatted_history
        ]
        return jsonify({"reply": bot_reply})

    media_data = {"movies": [], "tv_shows": []}
    for media_list, media_type, key in [(movie_data, "movie", "movies"), (tv_show_data, "tv", "tv_shows")]:
        for media in media_list:
            title = media["title"]
            year = media["year"]
            
            # Try searching with year first
            url = f"https://api.themoviedb.org/3/search/{media_type}?api_key={TMDB_API_KEY}&query={title}&page=1&include_adult=true"
            if year:
                url += f"&year={year}"
            
            response = requests.get(url).json()
            results = response.get("results", [])
            
            # If no results found with year, try without year
            if not results and year:
                url = f"https://api.themoviedb.org/3/search/{media_type}?api_key={TMDB_API_KEY}&query={title}&page=1&include_adult=true"
                response = requests.get(url).json()
                results = response.get("results", [])
            
            # Try with include_video=true for newer releases
            if not results:
                url = f"https://api.themoviedb.org/3/search/{media_type}?api_key={TMDB_API_KEY}&query={title}&page=1&include_adult=true&include_video=true"
                response = requests.get(url).json()
                results = response.get("results", [])
            
            if not results:
                print(f"⚠️ No {media_type} results found for: {title}")
                # Still add the media to the response even if not found in TMDB, with a note
                poster_url = "https://via.placeholder.com/500x750?text=No+Image"
                media_data[key].append({
                    "title": title,
                    "year": year if year else "N/A",
                    "poster_url": poster_url,
                    "tmdb_link": "#",
                    "release_status": " (Not found in database)"
                })
                continue
                
            media_info = results[0]
            media_id = media_info.get("id")
            poster_path = media_info.get("poster_path")
            
            # Get release date for checking if it's recent or upcoming
            release_date = media_info.get("release_date") if media_type == "movie" else media_info.get("first_air_date")
            release_year = release_date[:4] if release_date else "Unknown"
            
            # Check if this is a recent or upcoming release
            is_recent = is_recent_release(release_date)
            is_upcoming = is_upcoming_release(release_date)
            release_status = ""
            if is_upcoming:
                release_status = " (UPCOMING)"
            elif is_recent:
                release_status = " (RECENT)"
            
            media_data[key].append({
                "title": media_info["title"] if media_type == "movie" else media_info["name"],
                "year": release_year,
                "poster_url": f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else "https://via.placeholder.com/500x750?text=No+Image",
                "tmdb_link": f"/{media_type}/{media_id}",
                "release_status": release_status
            })

    formatted_history.append(AIMessage(content=bot_reply))
    chat_sessions[session_id] = [
        {"type": "human", "content": msg.content} if isinstance(msg, HumanMessage)
        else {"type": "ai", "content": msg.content}
        for msg in formatted_history
    ]

    response_data = {"reply": bot_reply}
    if media_data["movies"]:
        response_data["movies"] = media_data["movies"]
    if media_data["tv_shows"]:
        response_data["tv_shows"] = media_data["tv_shows"]
    return jsonify(response_data)