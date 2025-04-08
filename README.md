# Movie and TV Show Recommendation App With AI

This is a Flask web application that allows users to get recommendations for movies and TV shows based on genres and specific titles. The application uses The Movie Database (TMDb) API to fetch movie and TV show data.

## Features

- Browse movies and TV shows by genre
- Get recommendations for movies and TV shows based on a searched title
- Display details and posters of movies and TV shows
- **New Feature:** Integrated chatbot using **LLaMA 3** for interactive recommendations
- **New Feature:** Automatically fetch **movie posters, names, and details** from TMDb based on chatbot recommendations
- **New Feature:** Display fetched details alongside chatbot replies, with **clickable posters or movie names** leading to the TMDb page
- **Complete UI Overhaul:** Redesigned the entire user interface using **Tailwind CSS** for a modern and responsive look
- **New Pages:** Added dedicated pages for **movie details** and **TV show details** to enhance user experience

## Live Demo

Check out the live demo of the application deployed on Render [here](https://tv-movie-recommendations.onrender.com/).

![Alt Text](https://github.com/RobinMillford/Tv-Movie-Recommendations/blob/main/Movie-Recommender-System%201.png)

![Alt Text](https://github.com/RobinMillford/Tv-Movie-Recommendations/blob/main/Recommendations%202.png)

![Alt Text](https://github.com/RobinMillford/Tv-Movie-Recommendations/blob/main/TV-Show-Recommender-System%201.png)

![Alt Text](https://github.com/RobinMillford/Tv-Movie-Recommendations/blob/main/TV-Show-Recommendations%202.png)

![Alt Text](https://github.com/RobinMillford/Tv-Movie-Recommendations/blob/main/FlickFinder%201.png)

![Alt Text](https://github.com/RobinMillford/Tv-Movie-Recommendations/blob/main/chatapi.png)

![Alt Text](https://github.com/RobinMillford/Tv-Movie-Recommendations/blob/main/Full%20system.png)

## Getting Started

### Prerequisites

- Python 3.7+
- A TMDb API key. You can get one by creating an account on [The Movie Database](https://www.themoviedb.org/) and requesting an API key.
- Groq API Key → Sign up at Groq API

### Installation

To set up the project locally, follow these steps:

1. Clone the repository:

   ```bash
   git clone https://github.com/RobinMillford/tv-movie-recommendations.git
   cd Tv-Movie-Recommendations
   ```

2. Create a virtual environment and activate it:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the root directory and add your API keys:

   ```env
   SECRET_KEY=your secret key
   TMDB_API_KEY=your_tmdb_api_key
   GROQ_API_KEY=your_groq_api_key
   ```

### Running the Application

1. Run the Flask application:

   ```bash
   python app.py
   ```

2. Open your web browser and go to `http://127.0.0.1:5000` to view the app.

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
│   ├── chat.html  # New: Chat interface for movie recommendations
│   ├── movie_detail.html  # New: Enhanced movie details display
│   ├── tv_detail.html  # New: Enhanced TV show details display
│   ├── actor_detail.html  # New: Actor details display
│   └── error.html  # New: Error message display
└── static/
    └── styles.css  # New: Custom styles for improved UI
```

## New Updates

### 🔹 **Added Chatbot Integration**

- Integrated **Groq API with LLaMA 3** for a more interactive and intelligent movie recommendation system.
- Users can now **chat with the bot** to get personalized recommendations.

### 🔹 **Enhanced Movie and TV Show Details Display**

- When the chatbot recommends a movie or TV show, it automatically fetches **posters, names, and details** from TMDb.
- **Posters and names are clickable**, leading to the TMDb page for more information.
- Improved layout for the hero section, ensuring all content fits properly without overlap.

### 🔹 **Complete UI Overhaul**

- Redesigned the entire user interface using **Tailwind CSS** for a modern and responsive look.
- Enhanced user experience with a more intuitive layout and design.

### 🔹 **Improved User Experience**

- Movie and TV show details now appear **alongside the chatbot's responses** for a more seamless experience.
- Optimized API calls to ensure faster loading times.
- Added functionality to show full cast and reviews with toggle buttons for better content management.

## Contributing

Feel free to submit issues and enhancement requests.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

- This application uses the [TMDb API](https://www.themoviedb.org/documentation/api) but is not endorsed or certified by TMDb.

### How to Use the Deployed Application

1. **Access the Application:**  
   Visit the live demo [here](https://tv-movie-recommendations.onrender.com/).

2. **Browse by Genre:**

   - Navigate to the genre pages to see movies or TV shows listed by genre.

3. **Get Recommendations:**
   - Use the chatbot to ask for movie or TV show recommendations based on your preferences.
   - Click on the movie posters or names to visit their TMDb page for more details.
