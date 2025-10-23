from flask import Flask
from flask_login import LoginManager
from .config import Config
from .db import DB
import re


login = LoginManager()
login.login_view = 'users.login'


def highlight_search(text, query):
    """Highlight search terms in text"""
    if not query or not text:
        return text
    
    # Escape special regex characters in query
    escaped_query = re.escape(query)
    # Create case-insensitive pattern
    pattern = re.compile(f'({escaped_query})', re.IGNORECASE)
    # Replace matches with highlighted version
    highlighted = pattern.sub(r'<span class="search-highlight">\1</span>', text)
    return highlighted


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.db = DB(app)
    login.init_app(app)
    
    # Register custom Jinja2 filter
    app.jinja_env.filters['highlight_search'] = highlight_search

    from .index import bp as index_bp
    app.register_blueprint(index_bp)

    from .users import bp as user_bp
    app.register_blueprint(user_bp)

    from .sellers import bp as sellers_bp
    app.register_blueprint(sellers_bp)

    from .wishlist import bp as wishlist_bp
    app.register_blueprint(wishlist_bp)

    from .reviews import bp as reviews_bp
    app.register_blueprint(reviews_bp)

    from .cart import bp as cart_bp
    app.register_blueprint(cart_bp)
    
    from .checkout import bp as checkout_bp
    app.register_blueprint(checkout_bp)

    from .orders import bp as orders_bp
    app.register_blueprint(orders_bp)
    return app
