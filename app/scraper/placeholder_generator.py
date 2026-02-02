"""
Generate placeholder SVG logos for sites without logos.
"""
import os
import hashlib


class PlaceholderGenerator:
    """Generate SVG placeholders for missing logos."""
    
    def __init__(self, placeholder_dir):
        self.placeholder_dir = placeholder_dir
        os.makedirs(placeholder_dir, exist_ok=True)
    
    def generate_placeholder(self, site_name, domain):
        """
        Generate a placeholder SVG logo.
        
        Args:
            site_name: Display name of the site
            domain: Domain name (for color generation)
            
        Returns:
            str: Relative path to the placeholder SVG
        """
        # Extract initials
        initials = self._extract_initials(site_name, domain)
        
        # Generate deterministic color from domain
        color_hue = self._domain_to_hue(domain)
        bg_color = f"hsl({color_hue}, 40%, 85%)"
        text_color = f"hsl({color_hue}, 40%, 35%)"
        
        # Create SVG
        svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="400" height="400" xmlns="http://www.w3.org/2000/svg">
  <rect width="400" height="400" fill="{bg_color}"/>
  <text x="200" y="200" text-anchor="middle" dy=".35em"
        font-family="system-ui, -apple-system, sans-serif" 
        font-size="140" font-weight="600" fill="{text_color}">
    {initials}
  </text>
</svg>'''
        
        # Save SVG
        filename = f"{self._slugify(domain)}.svg"
        filepath = os.path.join(self.placeholder_dir, filename)
        
        with open(filepath, 'w') as f:
            f.write(svg)
        
        return f"/static/placeholders/{filename}"
    
    def _extract_initials(self, site_name, domain):
        """Extract 1-2 letter initials from name or domain."""
        if site_name:
            words = site_name.strip().split()
            initials = ''.join([w[0].upper() for w in words[:2]])
            if initials:
                return initials
        
        # Fallback to domain
        domain_clean = domain.replace('www.', '').split('.')[0]
        return domain_clean[:2].upper()
    
    def _domain_to_hue(self, domain):
        """Convert domain to a hue value (0-360)."""
        hash_value = int(hashlib.md5(domain.encode()).hexdigest(), 16)
        return hash_value % 360
    
    def _slugify(self, text):
        """Convert text to URL-safe slug."""
        return text.replace('https://', '').replace('http://', '').replace('/', '-').replace('.', '-')
