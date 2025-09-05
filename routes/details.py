from flask import Blueprint, render_template
from api.tmdb_client import fetch_movie_details, fetch_tv_show_details, fetch_actor_details

details = Blueprint('details', __name__)

@details.route('/movie/<int:movie_id>')
def movie_detail(movie_id):
    try:
        movie = fetch_movie_details(movie_id)
        return render_template('movie_detail.html', movie=movie)
    except Exception as e:
        print(f"Error fetching movie details: {e}")
        return render_template('error.html', message="Could not fetch movie details. Please try again later.")

@details.route('/tv/<int:show_id>')
def tv_detail(show_id):
    try:
        show = fetch_tv_show_details(show_id)
        return render_template('tv_detail.html', show=show)
    except Exception as e:
        print(f"Error fetching TV show details: {e}")
        return render_template('error.html', message="Could not fetch TV show details. Please try again later.")

@details.route('/actor/<int:actor_id>')
def actor_detail(actor_id):
    try:
        actor = fetch_actor_details(actor_id)
        return render_template('actor_detail.html', actor=actor)
    except Exception as e:
        print(f"Error fetching actor details: {e}")
        return render_template('error.html', message="Could not fetch actor details. Please try again later.")