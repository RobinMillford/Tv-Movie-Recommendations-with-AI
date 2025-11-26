from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
import requests
import os
from api.chatbot import get_chatbot, clean_json_response, is_recent_release, is_upcoming_release, is_safety_model_response, extract_media_with_llm
from api.rag_helper import enhance_prompt_with_rag
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
    if current_user.is_authenticated:
        return render_template("model_selection.html")
    else:
        return render_template("model_selection_login_required.html")

@chat.route("/chat")
@login_required
def chat_page():
    model_name = request.args.get("model", "llama-3.3-70b-versatile")
    session_id = request.remote_addr
    if session_id not in chat_sessions:
        chat_sessions[session_id] = []
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

    formatted_history = [
        HumanMessage(content=msg["content"]) if msg["type"] == "human" else AIMessage(content=msg["content"])
        for msg in chat_sessions[session_id]
    ]
    formatted_history.append(HumanMessage(content=user_message))

    chat_history_str = "\n".join(
        f"{'User' if isinstance(msg, HumanMessage) else 'Assistant'}: {msg.content}"
        for msg in formatted_history[:-1]
    )
    
    
    # SMART RAG STRATEGY: Let LLM analyze if query is about recent/new content
    # LLM understands context better than keyword matching
    analysis_prompt = f"""Analyze this user query about movies/TV shows:

Query: "{user_message}"

Determine:
1. Is this asking about RECENT/NEW content (2022-2025)? Consider:
   - Words like: recent, new, latest, newest, current, modern, trending, fresh, hot
   - Years: 2022, 2023, 2024, 2025
   - Phrases: just released, came out, this year, brand new, popular now
   - Misspellings: recnt, latst, etc.
   
2. Extract any specific movie/TV show title mentioned
3. Extract year if mentioned

Return JSON: {{"is_recent_content_query": true/false, "title": "..." or null, "year": "..." or null, "confidence": "high/medium/low"}}

Examples:
- "movie like matrix" → {{"is_recent_content_query": false, "title": null, "year": null, "confidence": "high"}}
- "tv show like Black Rabbit" → {{"is_recent_content_query": false, "title": "Black Rabbit", "year": null, "confidence": "medium"}}
- "recent tv show like Black Rabbit" → {{"is_recent_content_query": true, "title": "Black Rabbit", "year": null, "confidence": "high"}}
- "suggest me tv show like 'All Her Fault' from 2025" → {{"is_recent_content_query": true, "title": "All Her Fault", "year": "2025", "confidence": "high"}}
- "new movies from 2025" → {{"is_recent_content_query": true, "title": null, "year": "2025", "confidence": "high"}}
- "what came out this year" → {{"is_recent_content_query": true, "title": null, "year": null, "confidence": "high"}}
- "trending shows" → {{"is_recent_content_query": true, "title": null, "year": null, "confidence": "medium"}}
- "hot new series" → {{"is_recent_content_query": true, "title": null, "year": null, "confidence": "high"}}

IMPORTANT: Return ONLY the JSON object, no markdown, no explanations."""

    try:
        analysis_response = get_chatbot(model_name).invoke(analysis_prompt)
        analysis_data = json.loads(clean_json_response(analysis_response.content))
        
        is_recent_query = analysis_data.get("is_recent_content_query", False)
        source_title = analysis_data.get("title")
        source_year = analysis_data.get("year")
        confidence = analysis_data.get("confidence", "medium")
        
        # Trigger RAG if LLM detected recent content query
        needs_rag = is_recent_query
        
        # Also trigger if year 2022-2025 is mentioned (high confidence)
        if source_year:
            try:
                year_int = int(source_year)
                if 2022 <= year_int <= 2025:
                    needs_rag = True
                    confidence = "high"
            except:
                pass
        
        if needs_rag:
            if source_title:
                print(f"🤖 LLM: Recent content query ({confidence} confidence) - '{source_title}' ({source_year or 'any year'})")
            else:
                print(f"🤖 LLM: Recent content query ({confidence} confidence) - triggering RAG")
        else:
            print(f"🤖 LLM: General/old content query - using LLM knowledge first")
        
    except Exception as e:
        print(f"⚠️  LLM analysis failed: {e}")
        # Fallback: Simple keyword detection as backup
        recent_keywords = ['recent', 'new', 'latest', '2024', '2025', '2023', 'trending', 'fresh', 'hot']
        needs_rag = any(keyword in user_message.lower() for keyword in recent_keywords)
        source_title = None
        source_year = None
        if needs_rag:
            print(f"🤖 Fallback: Keyword detection triggered RAG")
    
    if needs_rag:
        # Use RAG for recent content queries
        rag_prompt, rag_used, _ = enhance_prompt_with_rag(
            user_message, 
            chat_history_str,
            source_title=source_title,
            source_year=source_year
        )
        if rag_used:
            bot_response = get_chatbot(model_name).invoke(rag_prompt)
            bot_reply = f"🎬 *Using recent media database*\n\n{bot_response.content.strip()}"
        else:
            # RAG didn't find it, use LLM knowledge
            bot_response = get_chatbot(model_name).invoke(f"Conversation:\n{chat_history_str}\n\nUser: {user_message}")
            bot_reply = bot_response.content.strip()
    else:
        # Use LLM's knowledge for general queries
        enhanced_prompt = f"""You are a movie/TV recommendation assistant.

Conversation:
{chat_history_str}

User: {user_message}"""
        
        bot_response = get_chatbot(model_name).invoke(enhanced_prompt)
        bot_reply = bot_response.content.strip()

        if not bot_reply:
            return jsonify({"error": "Empty response"}), 500

        if is_safety_model_response(bot_reply, model_name):
            fallback_model = "llama-3.3-70b-versatile"
            bot_response = get_chatbot(fallback_model).invoke(enhanced_prompt)
            bot_reply = bot_response.content.strip()
            model_name = fallback_model

    # IMPROVED MEDIA EXTRACTION - Only skip for question-only responses
    should_extract_media = True
    bot_reply_lower = bot_reply.lower()
    
    # Only skip if response is ONLY asking questions (no recommendations)
    question_only_patterns = [
        "what kind of mood are you in",
        "what genres do you prefer", 
        "any recent titles you",
        "which streaming services",
        "tell me more about your preferences"
    ]
    
    is_question_only = False
    for pattern in question_only_patterns:
        if pattern in bot_reply_lower:
            is_question_only = True
            break
    
    # Check if very short question without recommendation keywords
    if bot_reply_lower.strip().endswith("?") and len(bot_reply.split()) < 20:
        if not any(keyword in bot_reply_lower for keyword in ["suggest", "recommend", "here are", "check out", "might enjoy", "try"]):
            is_question_only = True
    
    if is_question_only:
        should_extract_media = False
    
    if should_extract_media:
        llm_prompt = f"""
        You are an expert text analyzer. Extract **movie** and **TV show** titles with years from this response.
        Return only valid JSON with "movies" and "tv_shows" arrays.
        Each item: {{"title": "...", "year": ... or null}}
        
        **Chatbot Response:**
        "{bot_reply}"
        """
        analysis_response = get_chatbot(model_name).invoke(llm_prompt)
        try:
            cleaned_content = clean_json_response(analysis_response.content)
            analysis_data = json.loads(cleaned_content)
            movie_data = analysis_data.get("movies", [])
            tv_show_data = analysis_data.get("tv_shows", [])
        except json.JSONDecodeError:
            print(f"Invalid JSON from analysis: {analysis_response.content}")
            if is_safety_model_response(analysis_response.content, model_name):
                movie_data = []
                tv_show_data = []
            else:
                movie_data, tv_show_data = extract_media_with_llm(bot_reply, model_name)
    else:
        movie_data = []
        tv_show_data = []

    # Fallback extraction if needed
    if should_extract_media and not movie_data and not tv_show_data:
        from api.chatbot import extract_media_titles, identify_media_type
        
        potential_titles = extract_media_titles(bot_reply)
        year_matches = re.findall(r'\b(19|20)\d{2}\b', bot_reply)
        
        for i, title in enumerate(potential_titles[:10]):
            year_match = re.search(r'\b(19|20)\d{2}\b', title)
            year = int(year_match.group()) if year_match else None
            
            if not year and i < len(year_matches):
                year = int(year_matches[i])
                
            from api.chatbot import _clean_special_titles
            clean_title = _clean_special_titles(title.strip())
            media_type = identify_media_type(clean_title)
            
            if media_type in ['movie', 'anime']:
                movie_data.append({"title": clean_title, "year": year})
            else:
                tv_show_data.append({"title": clean_title, "year": year})

    if not movie_data and not tv_show_data:
        formatted_history.append(AIMessage(content=bot_reply))
        chat_sessions[session_id] = [
            {"type": "human", "content": msg.content} if isinstance(msg, HumanMessage)
            else {"type": "ai", "content": msg.content}
            for msg in formatted_history
        ]
        return jsonify({"reply": bot_reply})

    # Fetch media details from TMDb
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
            
            if not results and year:
                url = f"https://api.themoviedb.org/3/search/{media_type}?api_key={TMDB_API_KEY}&query={title}&page=1&include_adult=true"
                response = requests.get(url).json()
                results = response.get("results", [])
            
            if not results:
                url = f"https://api.themoviedb.org/3/search/{media_type}?api_key={TMDB_API_KEY}&query={title}&page=1&include_adult=true&include_video=true"
                response = requests.get(url).json()
                results = response.get("results", [])
            
            if not results:
                print(f"⚠️ No {media_type} results found for: {title}")
                media_data[key].append({
                    "title": title,
                    "year": year if year else "N/A",
                    "poster_url": "https://via.placeholder.com/500x750?text=No+Image",
                    "tmdb_link": "#",
                    "release_status": " (Not found in database)"
                })
                continue
                
            media_info = results[0]
            media_id = media_info.get("id")
            poster_path = media_info.get("poster_path")
            
            release_date = media_info.get("release_date") if media_type == "movie" else media_info.get("first_air_date")
            release_year = release_date[:4] if release_date else "Unknown"
            
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
