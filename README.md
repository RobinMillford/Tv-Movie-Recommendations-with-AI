# Flask Movie and TV Show Recommendation App

This is a Flask web application that allows users to get recommendations for movies and TV shows based on genres and specific titles. The application uses The Movie Database (TMDb) API to fetch movie and TV show data.

## Features

- Browse movies and TV shows by genre
- Get recommendations for movies and TV shows based on a searched title
- Display details and posters of movies and TV shows

## Live Demo

Check out the live demo of the application deployed on Render [here](https://tv-movie-recommendations.onrender.com/).

## Getting Started

### Prerequisites

- Python 3.7+
- A TMDb API key. You can get one by creating an account on [The Movie Database](https://www.themoviedb.org/) and requesting an API key.

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

4. Create a `.env` file in the root directory and add your TMDb API key:

   ```env
   TMDB_API_KEY=your_tmdb_api_key
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
└── static/
    ├── css/
    ├── js/
```

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
   - Use the search functionality to get recommendations based on a specific movie or TV show title.
