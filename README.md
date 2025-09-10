# Movie and TV Show Recommendation App With AI

A Flask web application for discovering and getting recommendations for movies, TV shows, and actors using TMDb API and an AI-powered chatbot via Groq API.

![MovieTvHub Interface](images/MovieTvHub-Discover-Movies-Shows-People-04-16-2025_11_22_PM.png)

## Key Features

- **Browse & Search**: Explore movies, TV shows, and actors by genre or through search
- **AI Chatbot**: Get intelligent recommendations using multiple LLM models via Groq API
- **Personalized Experience**: User profiles with watchlists, wishlists, and viewing history
- **Detailed Information**: Comprehensive pages for movies, TV shows, and actors
- **Multiple Authentication Options**: Traditional username/password and Google OAuth
- **Persistent Storage**: PostgreSQL database and Cloudinary for profile images

## Live Demo

Check out the live demo on Render: [https://tv-movie-recommendations-with-ai.onrender.com/](https://tv-movie-recommendations.onrender.com/)

## Getting Started

### Prerequisites

- Python 3.7+
- API keys for TMDb, Groq, and optionally NewsAPI
- PostgreSQL database
- Cloudinary account (free tier available)
- Google OAuth credentials (for Google login)

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

4. Create a `.env` file with your API keys:

   ```env
   SECRET_KEY=your_secret_key
   TMDB_API_KEY=your_tmdb_api_key
   GROQ_API_KEY=your_groq_api_key
   NEWS_API_KEY=your_newsapi_key
   DATABASE_URL=postgresql://username:password@localhost:5432/moviehub
   CLOUDINARY_CLOUD_NAME=your_cloud_name
   CLOUDINARY_API_KEY=your_api_key
   CLOUDINARY_API_SECRET=your_api_secret

   # Google OAuth (optional)
   GOOGLE_CLIENT_ID=your_google_client_id
   GOOGLE_CLIENT_SECRET=your_google_client_secret
   ```

5. Google OAuth Setup:

   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the Google+ API
   - Go to "Credentials" and create an OAuth 2.0 Client ID
   - Set authorized redirect URIs to:
     - http://localhost:5000/google/callback (for local development)
     - https://yourdomain.com/google/callback (for production)
   - Copy the Client ID and Client Secret to your `.env` file

6. Run the application:

   ```bash
   python app.py
   ```

7. Open `http://127.0.0.1:5000` in your browser.

## Technical Implementation

### Authentication & User Management

- Secure user registration and login with Flask-Login
- Password hashing and validation requirements
- "Remember Me" functionality for 30-day persistent sessions
- Google OAuth integration for easy sign-in
- Profile management with customizable information

### Cloudinary Image Handling

- Profile images uploaded directly to Cloudinary with smart transformations
- 300x300px resizing with face detection
- Automatic quality optimization and format conversion
- CDN delivery for faster loading
- Backward compatibility with existing local images

### AI Chatbot

- Multiple LLM models via Groq API (LLaMA 3.3, LLaMA 3.1, etc.)
- Authentication protection (only for logged-in users)
- TMDb integration for fetching posters and details
- Enhanced handling of new and upcoming releases
- Theme-based recommendations from movie/TV show overviews

### Database Architecture

PostgreSQL database with:

- User accounts and profile information
- Media tracking (watchlist, wishlist, viewing history)
- Many-to-many relationships between users and media items

## Contributing

Submit issues or enhancement requests via GitHub. Pull requests are welcome!

## License

Licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Acknowledgements

- [TMDb API](https://www.themoviedb.org/documentation/api)
- [Groq](https://groq.com/) for AI chatbot functionality
- [Tailwind CSS](https://tailwindcss.com/) for styling
- [PostgreSQL](https://www.postgresql.org/) for database
- [Cloudinary](https://cloudinary.com/) for image handling
- [Google OAuth](https://developers.google.com/identity/protocols/oauth2) for authentication
