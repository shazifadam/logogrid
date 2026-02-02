from flask import Flask, render_template, request, redirect, session, flash
import json
import os
from dotenv import load_dotenv
from functools import wraps
import threading

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

ADMIN_USERNAME = 'encrea'
ADMIN_PASSWORD = 'EncreaStudio@2019'

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect('/admin/login')
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """Public frontend."""
    logos_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'logos.json')
    try:
        with open(logos_path, 'r') as f:
            logos = json.load(f)
    except FileNotFoundError:
        logos = []
    return render_template('index.html.jinja2', logos=logos)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect('/admin')
        else:
            flash('Invalid credentials', 'error')
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    """Admin logout."""
    session.pop('logged_in', None)
    flash('Logged out successfully', 'success')
    return redirect('/admin/login')

@app.route('/admin')
@login_required
def admin_dashboard():
    """Admin dashboard."""
    sites_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'sites.json')
    logos_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'logos.json')
    
    with open(sites_path, 'r') as f:
        sites = json.load(f)
    
    try:
        with open(logos_path, 'r') as f:
            logos = json.load(f)
    except FileNotFoundError:
        logos = []
    
    return render_template('admin_dashboard.html', sites=sites, logos=logos)

@app.route('/admin/add-site', methods=['POST'])
@login_required
def add_site():
    """Add new site."""
    sites_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'sites.json')
    
    url = request.form.get('url', '').strip()
    name = request.form.get('name', '').strip()
    category = request.form.get('category', 'government')
    fallback_logo_url = request.form.get('fallback_logo_url', '').strip()
    
    if not url or not name:
        flash('URL and Name are required', 'error')
        return redirect('/admin')
    
    # Load sites
    with open(sites_path, 'r') as f:
        sites = json.load(f)
    
    # Check duplicates
    if any(site['url'] == url for site in sites):
        flash('Site already exists', 'error')
        return redirect('/admin')
    
    # Create new site
    new_site = {
        'url': url,
        'name': name,
        'category': category,
        'country': 'MV',
        'enabled': True
    }
    
    if fallback_logo_url:
        new_site['fallback_logo_url'] = fallback_logo_url
    
    sites.append(new_site)
    
    # Save
    with open(sites_path, 'w') as f:
        json.dump(sites, f, indent=2)
    
    flash('Site added successfully! Click "Scrape All Sites" to fetch the logo.', 'success')
    return redirect('/admin')

@app.route('/admin/delete-site', methods=['POST'])
@login_required
def delete_site():
    """Delete site."""
    sites_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'sites.json')
    url = request.form.get('url', '').strip()
    
    if not url:
        flash('URL is required', 'error')
        return redirect('/admin')
    
    # Load sites
    with open(sites_path, 'r') as f:
        sites = json.load(f)
    
    # Filter out the site
    original_count = len(sites)
    sites = [site for site in sites if site['url'] != url]
    
    if len(sites) == original_count:
        flash('Site not found', 'error')
        return redirect('/admin')
    
    # Save
    with open(sites_path, 'w') as f:
        json.dump(sites, f, indent=2)
    
    flash('Site deleted successfully', 'success')
    return redirect('/admin')

@app.route('/admin/scrape-now', methods=['POST'])
@login_required
def scrape_now():
    """Trigger scraping."""
    def run_scraper():
        try:
            from app.refresh import LogoRefresher
            refresher = LogoRefresher()
            refresher.refresh_all()
            print("✅ Scraping completed!")
        except Exception as e:
            print(f"❌ Scraper error: {e}")
            import traceback
            traceback.print_exc()
    
    thread = threading.Thread(target=run_scraper)
    thread.daemon = True
    thread.start()
    
    flash('Scraping started! This may take a few minutes. Refresh the page to see updated status.', 'success')
    return redirect('/admin')

if __name__ == '__main__':
    app.run(debug=True)
