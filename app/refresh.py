"""
Main refresh script - scrapes all sites and generates output.
"""
import json
import os
from datetime import datetime
from urllib.parse import urlparse
import logging
from dotenv import load_dotenv

from app.scraper.logo_extractor import LogoExtractor
from app.scraper.image_processor import ImageProcessor
from app.scraper.placeholder_generator import PlaceholderGenerator

load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LogoRefresher:
    """Handles the full refresh process."""
    
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(__file__))
        
        self.sites_path = os.path.join(base_dir, 'config', 'sites.json')
        self.logos_path = os.path.join(base_dir, 'data', 'logos.json')
        self.cache_dir = os.path.join(base_dir, 'app', 'static', 'cached-logos')
        self.placeholder_dir = os.path.join(base_dir, 'app', 'static', 'placeholders')
        
        self.extractor = LogoExtractor(
            timeout=int(os.getenv('SCRAPER_TIMEOUT', 45)),
            max_retries=int(os.getenv('SCRAPER_MAX_RETRIES', 2)),
            user_agent=os.getenv('SCRAPER_USER_AGENT', 'LogoGrid/1.0')
        )
        
        self.processor = ImageProcessor(
            cache_dir=self.cache_dir,
            max_size_mb=int(os.getenv('IMAGE_MAX_SIZE_MB', 5)),
            output_size=int(os.getenv('IMAGE_OUTPUT_SIZE', 400))
        )
        
        self.generator = PlaceholderGenerator(self.placeholder_dir)
    
    def refresh_all(self):
        """Refresh all sites."""
        logger.info("Starting full refresh")
        
        # Load sites
        with open(self.sites_path, 'r') as f:
            sites = json.load(f)
        
        # Load existing logos for caching
        existing_logos = self._load_existing_logos()
        
        results = []
        
        for site in sites:
            if not site.get('enabled', True):
                logger.info(f"Skipping disabled site: {site['url']}")
                continue
            
            logger.info(f"Processing: {site['url']}")
            result = self._process_site(site, existing_logos)
            results.append(result)
        
        # Save results
        with open(self.logos_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Refresh complete: {len(results)} sites processed")
        
        return results
    
    def refresh_single(self, site_url):
        """Refresh a single site."""
        # Load sites
        with open(self.sites_path, 'r') as f:
            sites = json.load(f)
        
        # Find the site
        site = next((s for s in sites if s['url'] == site_url), None)
        if not site:
            raise ValueError(f"Site not found: {site_url}")
        
        # Load existing logos
        existing_logos = self._load_existing_logos()
        
        # Process the site
        result = self._process_site(site, existing_logos)
        
        # Update logos.json
        logos = self._load_existing_logos()
        logos = [l for l in logos if l['site_url'] != site_url]
        logos.append(result)
        
        with open(self.logos_path, 'w') as f:
            json.dump(logos, f, indent=2)
        
        return result
    
    def _process_site(self, site, existing_logos):
        """Process a single site."""
        site_url = site['url']
        domain = urlparse(site_url).netloc
        domain_slug = domain.replace('.', '-')
        
        # Try to extract logo
        extraction = self.extractor.extract_logo(site_url)
        
        logo_url = None
        status = 'error'
        error_message = extraction.get('error')
        
        if extraction['status'] == 'ok' and extraction['logo_url']:
            # Try to process the image
            try:
                processed = self.processor.process_logo(
                    extraction['logo_url'],
                    domain_slug
                )
                logo_url = processed['cached_path']
                status = 'ok'
                error_message = None
                
            except Exception as e:
                logger.error(f"Failed to process logo for {site_url}: {e}")
                # Try fallback URL
                if site.get('fallback_logo_url'):
                    logo_url = site['fallback_logo_url']
                    status = 'fallback'
                else:
                    # Generate placeholder
                    logo_url = self.generator.generate_placeholder(
                        site.get('name', domain),
                        domain
                    )
                    status = 'fallback'
        else:
            # No logo found - try fallback or generate placeholder
            if site.get('fallback_logo_url'):
                logo_url = site['fallback_logo_url']
                status = 'fallback'
            else:
                logo_url = self.generator.generate_placeholder(
                    site.get('name', domain),
                    domain
                )
                status = 'fallback'
        
        return {
            'site_url': site_url,
            'display_name': site.get('name', domain),
            'logo_url': logo_url,
            'status': status,
            'last_checked_at': datetime.utcnow().isoformat() + 'Z',
            'extraction_method': extraction.get('method', 'none'),
            'error_message': error_message,
            'category': site.get('category'),
            'country': site.get('country')
        }
    
    def _load_existing_logos(self):
        """Load existing logos.json."""
        if os.path.exists(self.logos_path):
            with open(self.logos_path, 'r') as f:
                return json.load(f)
        return []


def main():
    """CLI entry point."""
    refresher = LogoRefresher()
    refresher.refresh_all()


if __name__ == '__main__':
    main()
