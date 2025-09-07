# File: models.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# Association table for many-to-many relationship between users and movies in watchlist
user_watchlist = db.Table('user_watchlist',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('media_id', db.Integer, db.ForeignKey('media_item.id'), primary_key=True),
    db.Column('media_type', db.String(20), primary_key=True),  # 'movie' or 'tv'
    db.Column('date_added', db.DateTime, default=datetime.utcnow)
)

# Association table for many-to-many relationship between users and movies in wishlist
user_wishlist = db.Table('user_wishlist',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('media_id', db.Integer, db.ForeignKey('media_item.id'), primary_key=True),
    db.Column('media_type', db.String(20), primary_key=True),  # 'movie' or 'tv'
    db.Column('date_added', db.DateTime, default=datetime.utcnow)
)

# Table for user viewing history
user_viewed = db.Table('user_viewed',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('media_id', db.Integer, db.ForeignKey('media_item.id'), primary_key=True),
    db.Column('media_type', db.String(20), primary_key=True),  # 'movie' or 'tv'
    db.Column('date_viewed', db.DateTime, default=datetime.utcnow),
    db.Column('rating', db.Integer)  # Optional rating from 1-10
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)  # Increased length to accommodate longer hashes
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Profile information
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    bio = db.Column(db.Text)
    profile_picture = db.Column(db.String(200))
    
    # Relationships
    watchlist = db.relationship('MediaItem', secondary=user_watchlist, lazy='subquery',
        backref=db.backref('watchlisted_by', lazy=True))
    wishlist = db.relationship('MediaItem', secondary=user_wishlist, lazy='subquery',
        backref=db.backref('wishlisted_by', lazy=True))
    viewed_media = db.relationship('MediaItem', secondary=user_viewed, lazy='subquery',
        backref=db.backref('viewed_by', lazy=True))
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class MediaItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tmdb_id = db.Column(db.Integer, unique=True, nullable=False)
    media_type = db.Column(db.String(20), nullable=False)  # 'movie' or 'tv'
    title = db.Column(db.String(200), nullable=False)
    release_date = db.Column(db.Date)
    poster_path = db.Column(db.String(200))
    overview = db.Column(db.Text)
    rating = db.Column(db.Float)
    
    def __repr__(self):
        return f'<MediaItem {self.title}>'