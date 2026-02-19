"""
SkyModderAI - Business Community Blueprint

Free directory + Paid advertising:
- Free: Business directory listing
- Paid: Advertising ($5/1000 clicks, $50/10000 clicks)

Free to join, always.
Trust is behavioral (from verified platform activity).
Directory and advertising are separate.
Contact is gated by mutual consent.
Manual approval only.
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session, flash
from datetime import datetime

from business_service import get_business_service

business_bp = Blueprint('business', __name__, url_prefix='/business')


@business_bp.route('/')
def hub_landing():
    """Business community landing page - Education Hub with directory preview."""
    business_service = get_business_service()
    
    # Get featured businesses (top trust scores)
    featured = business_service.get_directory({'tier': 'trusted'})[:3]
    
    # Get education categories
    from config_loader import get_config_loader
    config = get_config_loader()
    hub_config = config._load_yaml(
        config.config_dir / 'hub_content.yaml'
    )
    categories = hub_config.get('categories', [])
    
    return render_template('business/hub.html', 
                         categories=categories,
                         featured=featured)


@business_bp.route('/directory')
def directory():
    """Searchable business directory."""
    business_service = get_business_service()
    
    # Get filters from query params
    filters = {
        'category': request.args.get('category'),
        'game': request.args.get('game'),
        'tier': request.args.get('tier'),
        'q': request.args.get('q')
    }
    
    # Remove None values
    filters = {k: v for k, v in filters.items() if v}
    
    # Get businesses
    businesses = business_service.get_directory(filters)
    
    # Get categories for filter dropdown
    from config_loader import get_config_loader
    config = get_config_loader()
    categories = config._load_yaml(
        config.config_dir / 'business_categories.yaml'
    ).get('approved', [])
    
    return render_template('business/directory.html',
                         businesses=businesses,
                         categories=categories,
                         filters=filters)


@business_bp.route('/directory/<slug>')
def profile(slug):
    """Individual business profile."""
    business_service = get_business_service()
    
    business = business_service.get_business_by_slug(slug)
    
    if not business:
        return render_template('error.html', code=404, message="Business not found"), 404
    
    # Get trust score
    trust = business_service.get_trust_score(business['id'])
    
    # Check if user can vote
    can_vote = 'user_email' in session
    
    # Check if user can connect (must be logged in and have own business)
    can_connect = 'user_email' in session  # Simplified for now
    
    return render_template('business/profile.html',
                         business=business,
                         trust=trust,
                         can_vote=can_vote,
                         can_connect=can_connect)


@business_bp.route('/join', methods=['GET', 'POST'])
def join():
    """Free business registration."""
    business_service = get_business_service()
    
    if request.method == 'POST':
        # Get form data
        data = {
            'name': request.form.get('company_name'),
            'website': request.form.get('website'),
            'category': request.form.get('category'),
            'tagline': request.form.get('tagline', ''),
            'description': request.form.get('description', ''),
            'logo_url': request.form.get('logo_url', ''),
            'contact_email': request.form.get('contact_email'),
            'public_contact_method': request.form.get('public_contact_method', 'form'),
            'public_contact_value': request.form.get('public_contact_value', ''),
            'secondary_categories': request.form.getlist('secondary_categories'),
            'relevant_games': request.form.getlist('relevant_games')
        }
        
        # Register business
        owner_email = session.get('user_email')
        business_id = business_service.register_business(data, owner_email)
        
        if business_id:
            flash('Your business has been submitted for review. We\'ll approve it within 7 days.', 'success')
            return redirect(url_for('business.applied'))
        else:
            flash('Failed to register business. Please try again.', 'error')
    
    # GET - show form
    categories = get_approved_categories()
    return render_template('business/join.html', categories=categories)


@business_bp.route('/applied')
def applied():
    """Application submitted confirmation."""
    return render_template('business/applied.html')


@business_bp.route('/hub')
def education_hub():
    """Education resource center."""
    from config_loader import get_config_loader
    config = get_config_loader()
    hub_config = config._load_yaml(
        config.config_dir / 'hub_content.yaml'
    )
    categories = hub_config.get('categories', [])
    
    # Get featured businesses
    business_service = get_business_service()
    featured = business_service.get_directory({'tier': 'trusted'})[:3]
    
    return render_template('business/hub.html',
                         categories=categories,
                         featured=featured)


@business_bp.route('/hub/<category>')
def hub_category(category):
    """Resource category page."""
    business_service = get_business_service()

    # Get resources from database for this category
    resources = business_service.get_hub_resources(category)

    # Also load static content from config as fallback
    from config_loader import get_config_loader
    config = get_config_loader()
    hub_config = config._load_yaml(
        config.config_dir / 'hub_content.yaml'
    )

    # Find category info
    category_info = None
    for cat in hub_config.get('categories', []):
        if cat.get('id') == category:
            category_info = cat
            break

    # Get featured businesses
    featured = business_service.get_directory({'tier': 'trusted'})[:3]

    return render_template('business/hub_category.html',
                         category=category,
                         category_info=category_info,
                         resources=resources,
                         featured=featured)


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
    
    business_service = get_business_service()
    
    # Get user's businesses
    db = get_db()
    businesses = db.execute("""
        SELECT * FROM businesses WHERE owner_email = ?
    """, (session['user_email'],)).fetchall()
    
    # Get metrics for each business
    business_metrics = []
    for biz in businesses:
        trust = business_service.get_trust_score(biz['id'])
        business_metrics.append({
            'business': biz,
            'trust': trust
        })
    
    return render_template('business/dashboard.html',
                         businesses=business_metrics,
                         metrics={})


@business_bp.route('/api/vote', methods=['POST'])
def vote():
    """Vote on a business."""
    if 'user_email' not in session:
        return jsonify({'error': 'Login required'}), 401
    
    data = request.get_json() or {}
    business_id = data.get('business_id')
    score = data.get('score')
    context = data.get('context', '')
    
    if not business_id or not score:
        return jsonify({'error': 'Business ID and score required'}), 400
    
    if score < 1 or score > 5:
        return jsonify({'error': 'Score must be between 1 and 5'}), 400
    
    business_service = get_business_service()
    success = business_service.vote(business_id, session['user_email'], score, context)
    
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Failed to record vote'}), 500


@business_bp.route('/api/flag', methods=['POST'])
def flag():
    """Flag a business for review."""
    if 'user_email' not in session:
        return jsonify({'error': 'Login required'}), 401
    
    data = request.get_json() or {}
    business_id = data.get('business_id')
    reason = data.get('reason')
    detail = data.get('detail', '')
    
    if not business_id or not reason:
        return jsonify({'error': 'Business ID and reason required'}), 400
    
    business_service = get_business_service()
    success = business_service.flag(business_id, session['user_email'], reason, detail)
    
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Failed to record flag'}), 500


@business_bp.route('/api/connect', methods=['POST'])
def connect():
    """Request introduction to another business."""
    if 'user_email' not in session:
        return jsonify({'error': 'Login required'}), 401
    
    data = request.get_json() or {}
    target_id = data.get('target_id')
    message = data.get('message', '')
    
    if not target_id:
        return jsonify({'error': 'Target business ID required'}), 400
    
    # Get requester's business
    db = get_db()
    requester = db.execute("""
        SELECT id FROM businesses WHERE owner_email = ?
    """, (session['user_email'],)).fetchone()
    
    if not requester:
        return jsonify({'error': 'You must have a registered business'}), 400
    
    # Create connection request
    try:
        db.execute("""
            INSERT INTO business_connections (requester_id, target_id, message, requested_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, (requester['id'], target_id, message))
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Helper functions

def get_approved_categories():
    """Get approved business categories from config."""
    from config_loader import get_config_loader
    config = get_config_loader()
    categories_config = config._load_yaml(
        config.config_dir / 'business_categories.yaml'
    )
    return categories_config.get('approved', [])


def get_db():
    """Get database connection."""
    from db import get_db as get_database
    return get_database()
