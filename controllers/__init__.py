# controllers/__init__.py
from flask import Blueprint
from .auth_controller import auth_bp
from .election_controller import election_bp
from .vote_controller import vote_bp
from .admin_controller import admin_bp

def init_app(app):
    """Initialize all controllers with the app"""
    app.register_blueprint(auth_bp)
    app.register_blueprint(election_bp)
    app.register_blueprint(vote_bp)
    app.register_blueprint(admin_bp)