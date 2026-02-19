"""
SkyModderAI - Business Community Blueprint

Free, trust-ranked professional directory for gaming/modding businesses.
- Free to join, always
- Trust is behavioral (from verified platform activity)
- Directory and advertising are separate
- Contact is gated by mutual consent
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, g, session
from datetime import datetime

business_bp = Blueprint('business', __name__, url_prefix='/business')


@business_bp.route('/')
def hub_landing():
    """Business community landing page - redirects to education hub."""
    # Redirect to education hub as the main landing
    from config_loader import get_config_loader
    config = get_config_loader()
    hub_config = config._load_yaml(
        config.config_dir / 'hub_content.yaml'
    )
    categories = hub_config.get('categories', [])
    
    return render_template('business/hub.html', 
                         categories=categories,
                         featured=[])


@business_bp.route('/directory')
def directory():
    """Searchable business directory."""
    category = request.args.get('category')
    game = request.args.get('game')
    tier = request.args.get('tier')
    query = request.args.get('q')
    
    # Placeholder - will be populated from database
    businesses = []
    
    return render_template('business/directory.html', 
                         businesses=businesses,
                         category=category,
                         game=game,
                         tier=tier,
                         query=query)


@business_bp.route('/directory/<slug>')
def profile(slug):
    """Individual business profile."""
    # Placeholder
    return render_template('business/profile.html', 
                         business={'name': 'Coming Soon', 'slug': slug}), 404


@business_bp.route('/join', methods=['GET', 'POST'])
def join():
    """Free business registration."""
    if request.method == 'POST':
        # Will be implemented with database
        return redirect(url_for('business.applied'))
    
    categories = get_approved_categories()
    return render_template('business/join.html', categories=categories)


@business_bp.route('/applied')
def applied():
    """Application submitted confirmation."""
    return render_template('business/applied.html')


@business_bp.route('/hub')
def education_hub():
    """Education resource center."""
    categories = get_hub_categories()
    return render_template('business/hub.html', 
                         categories=categories,
                         featured=[])


@business_bp.route('/hub/<category>')
def hub_category(category):
    """Resource category page."""
    resources = []  # Will be populated from database
    return render_template('business/hub_category.html',
                         category=category,
                         resources=resources)


@business_bp.route('/advertising')
def advertising():
    """Business advertising (paid sponsors) - $5/1000 clicks."""
    pricing = {
        'cpm': 5.00,  # $5 per 1,000 clicks
        'bulk_clicks': 10000,
        'bulk_price': 50.00,  # $50 for 10,000 clicks
        'cost_per_click': 0.005  # $0.005 per click
    }
    return render_template('business/advertising.html', pricing=pricing)


@business_bp.route('/dashboard')
def dashboard():
    """Authenticated business dashboard."""
    if 'user_email' not in session:
        return redirect(url_for('auth.login', next='/business/dashboard'))
    
    # Will show business metrics, trust score, connections
    return render_template('business/dashboard.html',
                         business=None,
                         trust=None,
                         connections=[],
                         metrics={})


@business_bp.route('/partners')
def partners():
    """Partner discovery (filtered directory)."""
    return render_template('business/partners.html', partners=[])


# Helper functions

def get_approved_categories():
    """Get approved business categories from config."""
    from config_loader import get_config_loader
    config = get_config_loader()
    categories_config = config._load_yaml(
        config.config_dir / 'business_categories.yaml'
    )
    return categories_config.get('approved', [])


def get_hub_categories():
    """Get education hub categories from config."""
    from config_loader import get_config_loader
    config = get_config_loader()
    hub_config = config._load_yaml(
        config.config_dir / 'hub_content.yaml'
    )
    return hub_config.get('categories', [])
