"""
Water meter type detection and reading extraction using color analysis and OCR.
"""

import numpy as np
from PIL import Image
import pytesseract
import cv2
import re
import os
from pathlib import Path

# Configure tesseract executable path (Windows default installation)
if os.name == 'nt':  # Windows
    tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    if os.path.exists(tesseract_path):
        pytesseract.pytesseract.tesseract_cmd = tesseract_path


def extract_meter_display(image_path, output_folder=None, debug=False):
    """
    Extract the meter display region from the center of the image.
    Uses color detection to find the dark display area surrounded by lighter meter body.
    
    Args:
        image_path: Path to the image file
        output_folder: Optional folder to save extracted display images
        debug: Print debug information
        
    Returns:
        numpy array of the extracted meter display region, or None if failed
    """
    try:
        # Open and read the image
        image = Image.open(image_path)
        img_array = np.array(image)
        
        # Get image dimensions
        height, width = img_array.shape[:2]
        
        # First do a rough crop to the center area where display should be
        rough_crop_x1 = int(width * 0.2)
        rough_crop_x2 = int(width * 0.8)
        rough_crop_y1 = int(height * 0.35)
        rough_crop_y2 = int(height * 0.70)
        
        rough_cropped = img_array[rough_crop_y1:rough_crop_y2, rough_crop_x1:rough_crop_x2]
        
        # Convert to RGB if needed
        if len(rough_cropped.shape) == 2:
            rough_cropped_rgb = cv2.cvtColor(rough_cropped, cv2.COLOR_GRAY2RGB)
        else:
            rough_cropped_rgb = rough_cropped.copy()
        
        # Look for the very dark digital display area (almost black background with dark numbers)
        # The display background is around RGB #2f302a to #454135 (47-69 range)
        # We want to find this specific dark rectangle, not just any dark area
        
        # Create mask for very dark areas (the digital display)
        # Relax the range a bit to catch more of the display
        dark_lower = np.array([20, 20, 15])  # Wider range below
        dark_upper = np.array([85, 85, 80])  # Wider range above
        dark_mask = cv2.inRange(rough_cropped_rgb, dark_lower, dark_upper)
        
        # Apply morphological operations to clean up and connect display pixels
        kernel_small = np.ones((3, 3), np.uint8)
        kernel_large = np.ones((10, 10), np.uint8)
        dark_mask = cv2.morphologyEx(dark_mask, cv2.MORPH_CLOSE, kernel_large)
        dark_mask = cv2.morphologyEx(dark_mask, cv2.MORPH_OPEN, kernel_small)
        
        # Find contours of dark areas
        contours, _ = cv2.findContours(dark_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        best_display = None
        best_score = 0
        
        if contours:
            # Find best rectangular contour that looks like a digital display
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                area = w * h
                
                # Digital displays are typically wider than tall (landscape orientation)
                # And should be reasonably sized (at least 100x30 pixels or so)
                if w > 80 and h > 20 and area > 2000:
                    # Calculate aspect ratio (width/height) - display should be 2:1 to 5:1
                    aspect_ratio = w / h
                    
                    # Score based on aspect ratio and size
                    # Prefer aspect ratios between 2.5 and 4.5
                    if 2.0 < aspect_ratio < 6.0:
                        score = area * (1.0 / abs(aspect_ratio - 3.5) if aspect_ratio != 3.5 else area)
                        
                        if score > best_score:
                            best_score = score
                            best_display = (x, y, w, h)
        
        if best_display:
            x, y, w, h = best_display
            
            # Add generous padding around the detected region to avoid cutting off numbers
            # Use proportional padding - about 15% of width/height
            padding_x = max(20, int(w * 0.15))
            padding_y = max(15, int(h * 0.15))
            
            x = max(0, x - padding_x)
            y = max(0, y - padding_y)
            w = min(rough_cropped.shape[1] - x, w + 2*padding_x)
            h = min(rough_cropped.shape[0] - y, h + 2*padding_y)
            
            # Extract the display region
            meter_display = rough_cropped[y:y+h, x:x+w]
            
            if debug:
                aspect = w / h if h > 0 else 0
                print(f"  Detected display region: {w}x{h} pixels (aspect ratio: {aspect:.2f})")
        else:
            # Fallback to center-focused fixed crop if detection fails
            if debug:
                print(f"  Display detection failed, using fallback crop")
            # Use a more generous fallback that captures the full center area
            crop_x1 = int(rough_cropped.shape[1] * 0.10)
            crop_x2 = int(rough_cropped.shape[1] * 0.90)
            crop_y1 = int(rough_cropped.shape[0] * 0.15)
            crop_y2 = int(rough_cropped.shape[0] * 0.70)
            meter_display = rough_cropped[crop_y1:crop_y2, crop_x1:crop_x2]
        
        # Save the extracted display if output folder is provided
        if output_folder:
            output_path = Path(output_folder)
            output_path.mkdir(exist_ok=True)
            
            # Create filename for extracted display
            stem = Path(image_path).stem
            output_file = output_path / f"{stem}_display.jpg"
            
            # Save as image
            display_image = Image.fromarray(meter_display)
            display_image.save(output_file)
            
            if debug:
                print(f"  Saved meter display: {output_file}")
        
        return meter_display
        
    except Exception as e:
        if debug:
            print(f"Error extracting meter display from {image_path}: {e}")
        return None


def detect_water_meter_type(image_path, debug=False):
    """
    Detect if the water meter image is for hot water (red) or cold water (blue).
    Uses HSV color space to detect hue.
    
    Args:
        image_path: Path to the image file
        debug: Print debug information
        
    Returns:
        'Hot Water' if red dominates, 'Cold Water' if blue dominates
    """
    try:
        # Open image and convert to RGB, resize for faster processing
        image = Image.open(image_path)
        image = image.resize((800,600))  # Resize for speed
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
        
        if debug:
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


def extract_meter_reading(image_path, debug=False, save_display=False, output_folder=None):
    """
    Extract the meter reading from a water meter image using OCR.
    
    Args:
        image_path: Path to the image file
        debug: Print debug information
        save_display: Save the extracted meter display region
        output_folder: Folder to save extracted displays (if save_display=True)
        
    Returns:
        String containing the meter reading (e.g., "00118.664") or None if not found
    """
    try:
        # First extract the meter display region
        if save_display and output_folder:
            meter_display = extract_meter_display(image_path, output_folder, debug)
        else:
            meter_display = extract_meter_display(image_path, None, debug)
        
        if meter_display is None:
            return None
        
        # Convert to grayscale
        if len(meter_display.shape) == 3:
            gray = cv2.cvtColor(meter_display, cv2.COLOR_RGB2GRAY)
        else:
            gray = meter_display.copy()
        
        # Resize to improve OCR - make it at least 1000 pixels wide
        height, width = gray.shape
        if width < 1000:
            scale = 1000 / width
            new_width = int(width * scale)
            new_height = int(height * scale)
            gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        
        # Try multiple preprocessing approaches
        processed_images = []
        
        # 1. Original grayscale
        processed_images.append(('original', gray))
        
        # 2. Contrast enhancement with CLAHE
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        processed_images.append(('clahe', enhanced))
        
        # 3. Simple threshold
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        processed_images.append(('otsu', thresh))
        
        # 4. Inverted (black background, white numbers)
        inverted = cv2.bitwise_not(gray)
        processed_images.append(('inverted', inverted))
        
        # 5. Sharpened
        kernel_sharpen = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(gray, -1, kernel_sharpen)
        processed_images.append(('sharpened', sharpened))
        
        # OCR configuration - try multiple PSM modes
        all_readings = []
        
        for method_name, processed in processed_images:
            # Try different PSM modes
            for psm in [7, 8, 13]:  # 7=single line, 8=single word, 13=raw line
                try:
                    config = f'--oem 3 --psm {psm} -c tessedit_char_whitelist=0123456789.'
                    text = pytesseract.image_to_string(processed, config=config)
                    text = text.strip().replace(' ', '').replace(',', '.')
                    
                    if debug and text:
                        print(f"    OCR ({method_name}, PSM {psm}): '{text}'")
                    
                    # Extract numeric patterns
                    matches = re.findall(r'\d+\.?\d*', text)
                    
                    for match in matches:
                        # Valid reading should have at least 3 digits total
                        if len(match.replace('.', '')) >= 3:
                            all_readings.append(match)
                except Exception as e:
                    if debug:
                        print(f"    OCR error ({method_name}, PSM {psm}): {e}")
                    continue
        
        if all_readings:
            # Prioritize longest reading with decimal point
            readings_with_decimal = [r for r in all_readings if '.' in r]
            
            if readings_with_decimal:
                best_reading = max(readings_with_decimal, key=lambda x: len(x.replace('.', '')))
            else:
                best_reading = max(all_readings, key=len)
            
            if debug:
                print(f"  OCR reading for {image_path.name}: {best_reading}")
            return best_reading
        else:
            if debug:
                print(f"  OCR: No reading found for {image_path.name}")
            return None
            
    except Exception as e:
        if debug:
            print(f"Error extracting meter reading from {image_path}: {e}")
        return None
