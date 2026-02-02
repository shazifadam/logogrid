"""
Image processing - download, resize, convert, and cache logos.
"""
import requests
from PIL import Image
from io import BytesIO
import hashlib
import os
import logging

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Process and cache logo images."""
    
    def __init__(self, cache_dir, max_size_mb=5, output_size=400):
        self.cache_dir = cache_dir
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.output_size = output_size
        
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
    
    def process_logo(self, logo_url, domain_slug):
        """
        Download and process a logo image.
        
        Args:
            logo_url: URL of the logo to download
            domain_slug: Slugified domain name for filename
            
        Returns:
            dict: {
                'cached_path': str,  # Relative path to cached image
                'etag': str,         # Hash of image content
                'dimensions': str,   # e.g., "180x180"
                'format': str        # e.g., "png", "webp"
            }
        """
        try:
            # Download image
            response = requests.get(
                logo_url,
                timeout=30,
                headers={'User-Agent': 'LogoGrid/1.0'}
            )
            response.raise_for_status()
            
            # Validate size
            if len(response.content) > self.max_size_bytes:
                raise ValueError(f"Image too large: {len(response.content)} bytes")
            
            # Validate content type
            content_type = response.headers.get('content-type', '')
            if 'image' not in content_type:
                raise ValueError(f"Invalid content type: {content_type}")
            
            # Open image
            img = Image.open(BytesIO(response.content))
            
            # Validate dimensions
            if img.width < 32 or img.height < 32:
                raise ValueError(f"Image too small: {img.width}x{img.height}")
            
            if img.width > 2000 or img.height > 2000:
                raise ValueError(f"Image too large: {img.width}x{img.height}")
            
            # Convert RGBA to RGB if needed
            if img.mode == 'RGBA':
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize if needed
            if img.width > self.output_size or img.height > self.output_size:
                img.thumbnail((self.output_size, self.output_size), Image.Resampling.LANCZOS)
            
            # Generate etag
            etag = hashlib.md5(response.content).hexdigest()[:12]
            
            # Save as PNG
            filename = f"{domain_slug}.png"
            filepath = os.path.join(self.cache_dir, filename)
            img.save(filepath, 'PNG', optimize=True)
            
            # Also save as WebP
            webp_filename = f"{domain_slug}.webp"
            webp_filepath = os.path.join(self.cache_dir, webp_filename)
            img.save(webp_filepath, 'WEBP', quality=85)
            
            logger.info(f"Processed logo: {logo_url} -> {filename}")
            
            return {
                'cached_path': f"/static/cached-logos/{filename}",
                'cached_path_webp': f"/static/cached-logos/{webp_filename}",
                'etag': etag,
                'dimensions': f"{img.width}x{img.height}",
                'format': 'png'
            }
            
        except Exception as e:
            logger.error(f"Error processing logo {logo_url}: {e}")
            raise
