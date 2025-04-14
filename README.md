# Movie and TV Show Recommendation App With AI

This is a Flask web application that allows users to discover and get recommendations for movies, TV shows, and actors using The Movie Database (TMDb) API and an AI-powered chatbot driven by **LLaMA 3**. The app offers a modern, responsive interface and interactive features for an enhanced user experience.

## Features

- Browse movies and TV shows by genre
- Search for movies, TV shows, and people (actors, directors, etc.)
- Get personalized recommendations for movies and TV shows based on titles or preferences
- Display detailed information, including posters, cast, and overviews
- **New Feature:** Integrated **search page** for movies, TV shows, and people with real-time TMDb results
- **New Feature:** Dedicated **person page** showcasing actor profiles, known works, and biographies
- **New Feature:** AI chatbot powered by **LLaMA 3** for interactive recommendations and queries about movies, TV shows, and people
- **New Feature:** Chatbot automatically fetches **posters, names, overviews, and details** from TMDb, with **clickable links** to TMDb pages
- **New Feature:** Chatbot uses **movie/TV show overviews** to analyze themes (e.g., secrets, technology) for smarter recommendations
- **Complete UI Overhaul:** Redesigned with **Tailwind CSS** for a modern, responsive look
- **Dedicated Pages:** Enhanced pages for **movie details**, **TV show details**, and **person details**

## Live Demo

Check out the live demo deployed on Render [here](https://tv-movie-recommendations.onrender.com/).

![Alt Text](https://github.com/RobinMillford/Tv-Movie-Recommendations/blob/main/Movie-Recommender-System%201.png)
![Alt Text](https://github.com/RobinMillford/Tv-Movie-Recommendations/blob/main/Movie-Recommender-System%202.png)
![Alt Text](https://github.com/RobinMillford/Tv-Movie-Recommendations/blob/main/TV-Show-Recommender-System%201.png)
![Alt Text](https://github.com/RobinMillford/Tv-Movie-Recommendations/blob/main/Details%20page.png)
![Alt Text](https://github.com/RobinMillford/Tv-Movie-Recommendations/blob/main/Cinebot.png)
![Alt Text](https://github.com/RobinMillford/Tv-Movie-Recommendations/blob/main/chatapi.png)
![Alt Text](https://github.com/RobinMillford/Tv-Movie-Recommendations/blob/main/Full%20system.png)

## Getting Started

### Prerequisites

- Python 3.7+
- A TMDb API key from [The Movie Database](https://www.themoviedb.org/)
- A Groq API key from [Groq](https://groq.com/)
- A NewsAPI key for entertainment news (optional, for `/news` page)

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/RobinMillford/tv-movie-recommendations.git
   cd Tv-Movie-Recommendations
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
   TMDB_API_KEY_2=your_tmdb_api_key_2
   GROQ_API_KEY=your_groq_api_key
   NEWS_API_KEY=your_newsapi_key
   ```

### Running the Application

1. Start the Flask app:

   ```bash
   python app.py
   ```

2. Open `http://127.0.0.1:5000` in your browser.

## Folder Structure

```
Tv-Movie-Recommendations/
├── app.py
├── requirements.txt
├── Procfile
├── .env
├── README.md
├── templates/
│   ├── index.html
│   ├── genre.html
│   ├── genre_not_found.html
│   ├── recommend.html
│   ├── no_results.html
│   ├── tv_genre.html
│   ├── tv_recommend.html
│   ├── chat.html
│   ├── movie_detail.html
│   ├── tv_detail.html
│   ├── actor_detail.html
│   ├── error.html
│   ├── movies.html
│ 
└── static/
    └── styles.css  # Tailwind CSS and custom styles
```

## New Updates

### 🔹 **Search Page for Movies, TV Shows, and People**

- Added a **index page** (`/`) allowing users to query movies, TV shows, and people in one place.
- Uses TMDb’s multi-search API for real-time results.
- Displays posters, titles, and brief details with links to respective detail pages.

### 🔹 **Person Details Page**

- Introduced a **person page** (`/actor/<id>`) for actors, directors, etc.
- Shows biography, known works, and profile images from TMDb.
- Links to related movies and TV shows for deeper exploration.

### 🔹 **Enhanced Chatbot**

- Upgraded chatbot with **LLaMA 3** via Groq API to handle queries about movies, TV shows, and people (e.g., “Who is Sophie Thatcher?”).
- Analyzes **movie/TV show overviews** to extract themes (e.g., deception, technology) for precise recommendations.
- Fetches **posters, names, overviews, and details** from TMDb, with **clickable links** to TMDb pages.
- Supports ambiguous queries by prompting for clarification (e.g., movie name and year).

### 🔹 **Improved UI and UX**

- Modernized interface with **Tailwind CSS** for responsiveness.
- Enhanced **movie**, **TV show**, and **person detail pages** with toggleable cast and reviews.
- Optimized API calls for faster load times.
- Chatbot responses display alongside fetched media details for seamless interaction.

## Contributing

Submit issues or enhancement requests via GitHub. Pull requests are welcome!

## License

Licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Acknowledgements

- Uses [TMDb API](https://www.themoviedb.org/documentation/api) (not endorsed by TMDb).
- Powered by [Groq](https://groq.com/) for AI chatbot functionality.
- Styled with [Tailwind CSS](https://tailwindcss.com/).

## How to Use the Deployed Application

1. **Access the App:**  
   Visit [https://tv-movie-recommendations.onrender.com/](https://tv-movie-recommendations.onrender.com/).

2. **Browse by Genre:**  
   Explore movies or TV shows by genre via dedicated pages.

3. **Search Content:**  
   Use the search bar to find movies, TV shows, or people, with results linking to detail pages.

4. **Get Recommendations:**  
   Chat with the AI bot to get tailored movie, TV show, or actor info. Click posters/names for TMDb details.

5. **View Details:**  
   Check out movie, TV show, or person pages for in-depth information.
