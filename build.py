"""
Build static site for Firebase deployment.
"""
import json
import os
import shutil
import sys
from jinja2 import Environment, FileSystemLoader

def url_for(endpoint, filename=None):
    """Mock Flask's url_for for static building."""
    if endpoint == 'static':
        return f"/{filename}"
    return "/"

def build_static_site(skip_scrape=False):
    """Generate static HTML from logos.json."""
    
    if not skip_scrape:
        print("Step 1: Running scraper to refresh logos...")
        try:
            from app.refresh import LogoRefresher
            refresher = LogoRefresher()
            refresher.refresh_all()
            print("Scraper completed successfully!")
        except Exception as e:
            print(f"Warning: Scraper failed: {e}")
            print("Continuing with existing data...")
    
    print("\nStep 2: Building static site...")
    
    # Load logos
    with open('data/logos.json', 'r') as f:
        logos = json.load(f)
    
    # Fix paths: remove /static/ prefix for public build
    for logo in logos:
        if logo['logo_url'].startswith('/static/'):
            logo['logo_url'] = logo['logo_url'].replace('/static/', '/')
    
    # Setup Jinja2 environment
    env = Environment(loader=FileSystemLoader('app/templates'))
    env.globals['url_for'] = url_for
    
    # Load and render template
    template = env.get_template('index.html.jinja2')
    html = template.render(logos=logos)
    
    # Create public directory structure
    os.makedirs('public', exist_ok=True)
    os.makedirs('public/css', exist_ok=True)
    os.makedirs('public/cached-logos', exist_ok=True)
    os.makedirs('public/placeholders', exist_ok=True)
    
    # Write HTML
    with open('public/index.html', 'w') as f:
        f.write(html)
    
    # Copy CSS
    shutil.copy('app/static/css/styles.css', 'public/css/styles.css')
    
    # Copy cached logos
    cache_src = 'app/static/cached-logos'
    if os.path.exists(cache_src):
        copied_logos = 0
        for file in os.listdir(cache_src):
            if file != '.gitkeep':
                src_path = os.path.join(cache_src, file)
                dst_path = os.path.join('public/cached-logos', file)
                shutil.copy(src_path, dst_path)
                copied_logos += 1
        if copied_logos > 0:
            print(f"Copied {copied_logos} cached logo files")
    
    # Copy placeholders
    placeholder_src = 'app/static/placeholders'
    if os.path.exists(placeholder_src):
        copied_placeholders = 0
        for file in os.listdir(placeholder_src):
            if file != '.gitkeep':
                src_path = os.path.join(placeholder_src, file)
                dst_path = os.path.join('public/placeholders', file)
                shutil.copy(src_path, dst_path)
                copied_placeholders += 1
        if copied_placeholders > 0:
            print(f"Copied {copied_placeholders} placeholder files")
    
    print(f"\nBuild completed successfully!")
    print(f"Total logos: {len(logos)}")
    print(f"Output directory: public/")

if __name__ == '__main__':
    skip_scrape = '--skip-scrape' in sys.argv
    build_static_site(skip_scrape=skip_scrape)
