# Movie and TV Show Recommendation App With AI

This is a Flask web application that allows users to discover and get recommendations for movies, TV shows, and actors using The Movie Database (TMDb API) and an AI-powered chatbot driven by **multiple LLM models** via Groq API. The app offers a modern, responsive interface and interactive features for an enhanced user experience.

![MovieTvHub Interface](images/MovieTvHub-Discover-Movies-Shows-People-04-16-2025_11_22_PM.png)

## Features

- Browse movies and TV shows by genre
- Search for movies, TV shows, and people (actors, directors, etc.)
- Get personalized recommendations for movies and TV shows based on titles or preferences
- Display detailed information, including posters, cast, and overviews
- **New Feature:** Integrated **search page** for movies, TV shows, and people with real-time TMDb results
- **New Feature:** Dedicated **person page** showcasing actor profiles, known works, and biographies
- **New Feature:** AI chatbot powered by **multiple LLM models** via Groq API for interactive recommendations and queries about movies, TV shows, and people
- **New Feature:** Chatbot automatically fetches **posters, names, overviews, and details** from TMDb, with **clickable links** to TMDb pages
- **New Feature:** Chatbot uses **movie/TV show overviews** to analyze themes (e.g., secrets, technology) for smarter recommendations
- **New Feature:** User authentication system with registration and login
- **New Feature:** Personalized user profiles with watchlist, wishlist, and viewing history
- **New Feature:** "Remember Me" functionality for persistent login sessions
- **New Feature:** Profile image upload capability
- **New Feature:** Personalized recommendations based on user's watchlist, wishlist, and viewing history
- **Backend:** PostgreSQL database for user account management and data persistence
- **Complete UI Overhaul:** Redesigned with **Tailwind CSS** for a modern, responsive look
- **Dedicated Pages:** Enhanced pages for **movie details**, **TV show details**, and **person details**

## How it's working

![Chatbot Diagram](images/chatbot_Diagram.png)

![Chat API](images/chatapi.png)

![Website Architecture](images/Website_arch.png)

## Live Demo

Check out the live demo deployed on Render [here](https://tv-movie-recommendations.onrender.com/).

![Movie Recommender System 1](images/Movie-Recommender-System%201.png)

![Movie Recommender System 2](images/Movie-Recommender-System%202.png)

![TV Show Recommender System](images/TV-Show-Recommender-System%201.png)

![Details Page](images/Details%20page.png)

![Actor Profile - Tom Cruise](images/Tom-Cruise-ActorHub-04-16-2025_11_25_PM.png)

![User Profile Page](images/Profile-MovieHub.jpg)

![CineBot Chat Interface](images/Cinebot.png)

## Getting Started

### Prerequisites

- Python 3.7+
- A TMDb API key from [The Movie Database](https://www.themoviedb.org/)
- A Groq API key from [Groq](https://groq.com/)
- A NewsAPI key for entertainment news (optional, for `/news` page)
- PostgreSQL database for user account management and data persistence

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/RobinMillford/tv-movie-recommendations.git
   cd Tv-Movie-Recommendations-with-AI
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the root directory with your API keys:

   ```env
   SECRET_KEY=your_secret_key
   TMDB_API_KEY=your_tmdb_api_key
   GROQ_API_KEY=your_groq_api_key
   NEWS_API_KEY=your_newsapi_key
   DATABASE_URL=postgresql://username:password@localhost:5432/moviehub
   ```

### Running the Application

1. Start the Flask app:

   ```bash
   python app.py
   ```

2. Open `http://127.0.0.1:5000` in your browser.

## Folder Structure

```
Tv-Movie-Recommendations-with-AI/
├── app.py
├── requirements.txt
├── Procfile
├── .env
├── README.md
├── LICENSE
├── .gitignore
├── DEPLOYMENT_GUIDE.md
├── AI_CHAT_AUTHENTICATION.md
├── RENDER_DEPLOYMENT_GUIDE.md
├── NEW_FEATURES_SUMMARY.md
├── api/
│   ├── __init__.py
│   ├── chatbot.py
│   └── tmdb_client.py
├── routes/
│   ├── __init__.py
│   ├── main.py
│   ├── chat.py
│   ├── details.py
│   ├── auth.py
│   └── news.py

├── templates/
│   ├── index.html
│   ├── genre.html
│   ├── genre_not_found.html
│   ├── recommend.html
│   ├── no_results.html
│   ├── tv_genre.html
│   ├── tv_recommend.html
│   ├── chat.html
│   ├── model_selection.html
│   ├── model_selection_login_required.html
│   ├── movie_detail.html
│   ├── tv_detail.html
│   ├── actor_detail.html
│   ├── error.html
│   ├── movies.html
│   ├── tv_shows.html
│   ├── news.html
│   ├── search_results.html
│   ├── not_found.html
│   ├── register.html
│   ├── login.html
│   ├── profile.html
│   ├── profile_recommendations.html
│   ├── edit_profile.html
│   ├── watchlist.html
│   ├── wishlist.html
│   └── viewed.html
├── static/
│   ├── favicon.ico
│   ├── favicon2.ico
│   ├── favicon3.ico
│   └── css/
│       └── style.css
└── images/
    ├── Cinebot.png
    ├── Details page.png
    ├── Movie-Recommender-System 1.png
    ├── Movie-Recommender-System 2.png
    ├── MovieTvHub-Discover-Movies-Shows-People-04-16-2025_11_22_PM.png
    ├── Profile-MovieHub.jpg
    ├── TV-Show-Recommender-System 1.png
    ├── Tom-Cruise-ActorHub-04-16-2025_11_25_PM.png
    ├── Website_arch.png
    ├── chatapi.png
    └── chatbot_Diagram.png
```

## New Updates

### 🔹 **User Authentication System**

- Added complete user registration and login system with secure password hashing
- Implemented email validation and password strength requirements during registration
- Added "Remember Me" functionality for persistent login sessions (30 days)
- Secure session management with Flask-Login

### 🔹 **Personalized User Profiles**

- Created user profile pages with customizable information (first name, last name, bio)
- Implemented profile image upload functionality with secure file handling
- Added personalized recommendations based on user's watchlist, wishlist, and viewing history
- Profile recommendations preview on the main profile page with "View All" option

### 🔹 **Media List Management**

- Added watchlist functionality to save movies and TV shows for later viewing
- Implemented wishlist feature for movies and TV shows users want to watch
- Created viewing history tracking to remember what users have watched
- Added status indicators throughout the application to show media list membership

### 🔹 **Search Page for Movies, TV Shows, and People**

- Added a **index page** (`/`) allowing users to query movies, TV shows, and people in one place.
- Uses TMDb's multi-search API for real-time results.
- Displays posters, titles, and brief details with links to respective detail pages.

### 🔹 **Person Details Page**

- Introduced a **person page** (`/actor/<id>`) for actors, directors, etc.
- Shows biography, known works, and profile images from TMDb.
- Links to related movies and TV shows for deeper exploration.

### 🔹 **Enhanced Chatbot**

- Upgraded chatbot with **multiple LLM models** via Groq API to handle queries about movies, TV shows, and people (e.g., "Who is Sophie Thatcher?").
- Analyzes **movie/TV show overviews** to extract themes (e.g., deception, technology) for precise recommendations.
- Fetches **posters, names, overviews, and details** from TMDb, with **clickable links** to TMDb pages.
- Supports ambiguous queries by prompting for clarification (e.g., movie name and year).
- **Enhanced for New Releases**: Improved handling of recent and upcoming movies, TV shows, and anime that LLMs might not have extensive knowledge about.
- **Authentication Protection**: AI chatbot is now only accessible to authenticated users for security and personalization.
- **Model Selection**: Users can choose from multiple available models for different needs and preferences.

### 🔹 **Improved UI and UX**

- Modernized interface with **Tailwind CSS** for responsiveness.
- Enhanced **movie**, **TV show**, and **person detail pages** with toggleable cast and reviews.
- Optimized API calls for faster load times.
- Chatbot responses display alongside fetched media details for seamless interaction.

## Chatbot Improvements

The chatbot has been significantly enhanced to better handle new releases and provide more accurate recommendations:

### Enhanced Media Detection for New Releases

- Implements date-based filtering to identify recent (within 6 months) and upcoming releases
- Uses flexible search strategies with `include_video=true` parameter for better detection
- Multi-stage search approach for comprehensive results
- Improved handling of formatted titles and special cases (e.g., "The Empire Strikes — The Dark Side (The Empire Strikes Back)")

### Improved Media Type Handling

- Heuristic-based classification for movies, TV shows, and anime
- Keyword databases for accurate categorization
- Specialized processing for different media types

### Better Response Quality

- Enhanced prompt engineering for more accurate media extraction
- Improved uncertainty detection that doesn't flag new releases as uncertain
- Robust error handling and fallback mechanisms

### Performance Optimizations

- In-memory caching for TMDB requests
- Request timeout and retry logic
- Optimized conversation history management

## User Authentication and Profile Features

### Registration Security

- Email format validation using regex patterns
- Password strength requirements (8+ characters, uppercase, lowercase, digit)
- Real-time password feedback during registration
- Duplicate username and email checking

### Login Enhancements

- "Remember Me" functionality for 30-day persistent sessions
- Secure password verification
- Clear error messages for failed login attempts

### Profile Management

- Customizable user profiles with first name, last name, and bio
- Profile image upload with secure file handling
- Personalized recommendations based on user's media lists
- Watchlist, wishlist, and viewing history management

### Media List Features

- Add/remove movies and TV shows to/from watchlist
- Add/remove movies and TV shows to/from wishlist
- Mark movies and TV shows as viewed
- Status indicators showing media list membership throughout the application

## Database Architecture

The application uses **PostgreSQL** as its backend database for robust data persistence and scalability:

### User Management

- User accounts with secure password hashing
- Profile information storage (names, bio, profile picture)
- Session management for authentication

### Media Tracking

- Watchlist for saving movies and TV shows for later viewing
- Wishlist for items users want to watch
- Viewing history to track what users have watched

### Data Relationships

- Many-to-many relationships between users and media items
- Association tables for watchlist, wishlist, and viewing history
- Support for both movies and TV shows with media type differentiation

## Contributing

Submit issues or enhancement requests via GitHub. Pull requests are welcome!

## License

Licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Acknowledgements

- Uses [TMDb API](https://www.themoviedb.org/documentation/api) (not endorsed by TMDb).
- Powered by [Groq](https://groq.com/) for AI chatbot functionality with multiple LLM models:
  - `llama-3.3-70b-versatile` (default, 70B parameters)
  - `llama-3.1-8b-instant` (fast response, 8B parameters)
  - `meta-llama/llama-guard-4-12b` (safety-focused, 12B parameters)
  - `openai/gpt-oss-120b` (open-source, 120B parameters)
  - `openai/gpt-oss-20b` (compact open-source, 20B parameters)
- Styled with [Tailwind CSS](https://tailwindcss.com/).
- Database powered by [PostgreSQL](https://www.postgresql.org/).

## How to Use the Deployed Application

1. **Access the App:**  
   Visit [https://tv-movie-recommendations.onrender.com/](https://tv-movie-recommendations.onrender.com/).

2. **Register an Account:**  
   Create a new account to access personalized features.

3. **Browse by Genre:**  
   Explore movies or TV shows by genre via dedicated pages.

4. **Search Content:**  
   Use the search bar to find movies, TV shows, or people, with results linking to detail pages.

5. **Manage Your Lists:**  
   Add movies and TV shows to your watchlist, wishlist, or mark as viewed.

6. **Get Personalized Recommendations:**  
   Visit your profile to see recommendations based on your media lists.

7. **Chat with AI:**  
   Use the AI chatbot (available only to logged-in users) to get tailored movie, TV show, or actor info. Click posters/names for TMDb details.

8. **View Details:**  
   Check out movie, TV show, or person pages for in-depth information.
