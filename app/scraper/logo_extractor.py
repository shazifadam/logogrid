"""
Logo extraction logic - implements priority-based logo discovery.
"""
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging
import time

logger = logging.getLogger(__name__)


class LogoExtractor:
    """Extracts logos from websites using multiple strategies."""
    
    def __init__(self, timeout=45, max_retries=2, user_agent=None):
        self.timeout = timeout
        self.max_retries = max_retries
        self.user_agent = user_agent or "LogoGrid/1.0 (+https://logogrid.example.com)"
        
    def extract_logo(self, url):
        """
        Extract logo from a website using priority-based methods.
        
        Returns:
            dict: {
                'logo_url': str or None,
                'method': str,
                'status': 'ok' | 'fallback' | 'error',
                'error': str or None
            }
        """
        try:
            html, final_url = self._fetch_page(url)
            
            if not html:
                return {
                    'logo_url': None,
                    'method': 'none',
                    'status': 'error',
                    'error': 'Failed to fetch page'
                }
            
            soup = BeautifulSoup(html, 'lxml')
            
            # Priority 1: Apple Touch Icon
            logo_url = self._extract_apple_touch_icon(soup, final_url)
            if logo_url:
                return {
                    'logo_url': logo_url,
                    'method': 'apple-touch-icon',
                    'status': 'ok',
                    'error': None
                }
            
            # Priority 2: Favicon variants
            logo_url = self._extract_favicon(soup, final_url)
            if logo_url:
                return {
                    'logo_url': logo_url,
                    'method': 'favicon',
                    'status': 'ok',
                    'error': None
                }
            
            # Priority 3: OG Image
            logo_url = self._extract_og_image(soup, final_url)
            if logo_url:
                return {
                    'logo_url': logo_url,
                    'method': 'og-image',
                    'status': 'ok',
                    'error': None
                }
            
            # Priority 4: Twitter Image
            logo_url = self._extract_twitter_image(soup, final_url)
            if logo_url:
                return {
                    'logo_url': logo_url,
                    'method': 'twitter-image',
                    'status': 'ok',
                    'error': None
                }
            
            # Priority 5: Header/Nav Logo
            logo_url = self._extract_header_logo(soup, final_url)
            if logo_url:
                return {
                    'logo_url': logo_url,
                    'method': 'header-logo',
                    'status': 'ok',
                    'error': None
                }
            
            # Priority 6: Common paths
            logo_url = self._try_common_paths(final_url)
            if logo_url:
                return {
                    'logo_url': logo_url,
                    'method': 'common-path',
                    'status': 'ok',
                    'error': None
                }
            
            # No logo found
            return {
                'logo_url': None,
                'method': 'none',
                'status': 'error',
                'error': 'No logo found'
            }
            
        except Exception as e:
            logger.error(f"Error extracting logo from {url}: {e}")
            return {
                'logo_url': None,
                'method': 'none',
                'status': 'error',
                'error': str(e)
            }
    
    def _fetch_page(self, url):
        """Fetch page HTML with retries."""
        headers = {
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        for attempt in range(self.max_retries + 1):
            try:
                response = requests.get(
                    url,
                    headers=headers,
                    timeout=self.timeout,
                    allow_redirects=True
                )
                response.raise_for_status()
                return response.text, response.url
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < self.max_retries:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    return None, None
    
    def _extract_apple_touch_icon(self, soup, base_url):
        """Extract apple-touch-icon."""
        links = soup.find_all('link', rel=lambda x: x and 'apple-touch-icon' in x.lower())
        
        # Prefer larger sizes
        for link in sorted(links, key=lambda x: self._get_icon_size(x), reverse=True):
            href = link.get('href')
            if href:
                return urljoin(base_url, href)
        return None
    
    def _extract_favicon(self, soup, base_url):
        """Extract favicon (prefer SVG, then PNG)."""
        # Try SVG favicon first
        svg_icon = soup.find('link', rel='icon', type='image/svg+xml')
        if svg_icon and svg_icon.get('href'):
            return urljoin(base_url, svg_icon['href'])
        
        # Try regular icons
        icons = soup.find_all('link', rel=lambda x: x and 'icon' in x.lower())
        
        for icon in icons:
            href = icon.get('href')
            if href and not href.endswith('.ico'):  # Avoid low-quality .ico
                return urljoin(base_url, href)
        
        return None
    
    def _extract_og_image(self, soup, base_url):
        """Extract Open Graph image."""
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            return urljoin(base_url, og_image['content'])
        return None
    
    def _extract_twitter_image(self, soup, base_url):
        """Extract Twitter card image."""
        twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
        if twitter_image and twitter_image.get('content'):
            return urljoin(base_url, twitter_image['content'])
        return None
    
    def _extract_header_logo(self, soup, base_url):
        """Extract logo from header/nav using heuristics."""
        containers = soup.select('header, nav, .header, .navbar, [role="banner"]')
        
        for container in containers:
            images = container.find_all('img')
            
            for img in images:
                score = self._score_logo_image(img)
                
                if score >= 4:  # Threshold for acceptance
                    src = img.get('src')
                    if src:
                        return urljoin(base_url, src)
        
        return None
    
    def _score_logo_image(self, img):
        """Score an image based on logo likelihood."""
        score = 0
        
        # Check alt text
        alt = img.get('alt', '').lower()
        if any(word in alt for word in ['logo', 'brand', 'site']):
            score += 3
        
        # Check src
        src = img.get('src', '').lower()
        if any(word in src for word in ['logo', 'brand']):
            score += 2
        
        # Check class
        classes = ' '.join(img.get('class', [])).lower()
        if any(word in classes for word in ['logo', 'brand', 'site-logo']):
            score += 2
        
        # Check dimensions (if available)
        width = self._parse_dimension(img.get('width'))
        height = self._parse_dimension(img.get('height'))
        
        if width and height:
            if 60 <= width <= 400 and 40 <= height <= 400:
                score += 1
            
            # Check aspect ratio
            ratio = width / height
            if 0.33 <= ratio <= 3.0:
                score += 1
        
        return score
    
    def _try_common_paths(self, base_url):
        """Try common logo paths."""
        parsed = urlparse(base_url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        
        common_paths = [
            '/logo.svg',
            '/logo.png',
            '/assets/logo.svg',
            '/assets/logo.png',
            '/images/logo.svg',
            '/images/logo.png',
            '/static/logo.svg',
            '/static/logo.png',
        ]
        
        headers = {'User-Agent': self.user_agent}
        
        for path in common_paths:
            url = base + path
            try:
                response = requests.head(url, headers=headers, timeout=5, allow_redirects=True)
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '')
                    if 'image' in content_type:
                        return url
            except:
                continue
        
        return None
    
    @staticmethod
    def _get_icon_size(link):
        """Extract size from icon link."""
        sizes = link.get('sizes', '')
        if 'x' in sizes:
            try:
                return int(sizes.split('x')[0])
            except:
                pass
        return 0
    
    @staticmethod
    def _parse_dimension(value):
        """Parse dimension from string or int."""
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            try:
                return int(value.replace('px', ''))
            except:
                pass
        return None
