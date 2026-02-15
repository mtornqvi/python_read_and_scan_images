"""
Water meter type detection using color analysis.
"""

import numpy as np
from PIL import Image


def detect_water_meter_type(image_path):
    """
    Detect if the water meter image is for hot water (red) or cold water (blue).
    Uses HSV color space to detect hue.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        'Hot Water' if red dominates, 'Cold Water' if blue dominates
    """
    try:
        # Open image and convert to RGB, resize for faster processing
        image = Image.open(image_path)
        image = image.resize((800, 600))  # Resize for speed
        image = image.convert('RGB')
        
        # Convert to numpy array (uint8 0-255)
        img_array = np.array(image).astype(float)
        
        # Extract RGB channels
        r = img_array[:, :, 0] / 255.0
        g = img_array[:, :, 1] / 255.0
        b = img_array[:, :, 2] / 255.0
        
        # Compute HSV components (vectorized)
        max_c = np.maximum(np.maximum(r, g), b)
        min_c = np.minimum(np.minimum(r, g), b)
        diff = max_c - min_c
        
        # Saturation
        saturation = np.where(max_c == 0, 0, diff / max_c)
        
        # Value
        value = max_c
        
        # Hue (0-1 scale)
        hue = np.zeros_like(max_c)
        
        # Red dominant
        mask = (max_c == r)
        hue[mask] = (60 * ((g[mask] - b[mask]) / (diff[mask] + 1e-10)) + 360) % 360
        
        # Green dominant
        mask = (max_c == g)
        hue[mask] = (60 * ((b[mask] - r[mask]) / (diff[mask] + 1e-10)) + 120)
        
        # Blue dominant
        mask = (max_c == b)
        hue[mask] = (60 * ((r[mask] - g[mask]) / (diff[mask] + 1e-10)) + 240)
        
        hue = hue / 360.0  # Convert to 0-1 scale
        
        # Only consider pixels with decent saturation and value (colored pixels)
        colored_mask = (saturation > 0.15) & (value > 0.25)
        
        # Hue ranges (in 0-1 scale, hue in degrees / 360):
        # Red: 345-360° (0.958-1.0) or 0-15° (0-0.042)
        # Blue: 200-250° (0.556-0.694)
        red_mask = colored_mask & ((hue < 0.042) | (hue > 0.958))
        blue_mask = colored_mask & (hue >= 0.52) & (hue <= 0.72)
        
        red_pixel_count = np.sum(red_mask)
        blue_pixel_count = np.sum(blue_mask)
        total_colored = np.sum(colored_mask)
        
        print(f"  Debug {image_path.name}: colored={total_colored}, red={red_pixel_count}({red_pixel_count*100/max(total_colored,1):.1f}%), blue={blue_pixel_count}({blue_pixel_count*100/max(total_colored,1):.1f}%)")
        
        # Decision based on which color has more pixels
        if red_pixel_count > blue_pixel_count:
            return 'Hot Water'
        elif blue_pixel_count > red_pixel_count:
            return 'Cold Water'
        else:
            return 'Unknown'
            
    except Exception as e:
        print(f"Error detecting water meter type from {image_path}: {e}")
        import traceback
        traceback.print_exc()
        return 'Unknown'
