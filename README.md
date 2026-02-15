# python_read_and_scan_images
Water Meter Reading Extraction Tool

## Description
This program processes JPG images of water meters from the `data` folder, automatically detects the meter type (hot/cold water), extracts the digital display region, attempts to read the meter value using OCR, and exports all information to an Excel spreadsheet in the `results` folder.

## Features
- **Image Scanning**: Processes all JPG images from the `data` folder
- **EXIF Metadata Extraction**: Retrieves date and time when each photo was taken
- **Meter Type Detection**: Automatically identifies hot water (red surrounding) vs cold water (blue surrounding) using HSV color analysis
- **Display Region Extraction** (v0.1 - works okish): Automatically crops the digital display area from water meter images using color-based detection
- **OCR Reading Extraction** (WIP - doesn't work): Attempts to read meter values from the extracted display regions (currently unreliable)
- **Excel Export**: Creates a comprehensive spreadsheet with filename, timestamp, meter type, and reading
- **Debug Output**: Saves extracted display regions to `results/meter_displays/` for troubleshooting

## Current Status
- ✅ EXIF metadata extraction: Working
- ✅ Meter type detection (hot/cold): Working
- ⚠️ Display cropping: v0.1 (works okish - most images crop correctly, some need adjustment)
- ❌ OCR reading extraction: WIP (doesn't work reliably yet)

## Installation

1. Create and activate a virtual environment (recommended):
```bash
python -m venv .venv
.venv\Scripts\activate  # On Windows
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Install Tesseract OCR:
```bash
winget install --id UB-Mannheim.TesseractOCR
```

## Usage

1. Place your water meter JPG images in the `data` folder
2. Run the script:
```bash
python scan_images.py
```
3. Find the generated Excel file in the `results` folder (named like `2026.02.15T10.46__images.xlsx`)
4. Check extracted display regions in `results/meter_displays/` for debugging

## Output Format
The program creates an Excel file with the following columns:
- **File Name**: Original image filename
- **Date/Time Taken**: When the photo was captured (from EXIF metadata)
- **Meter Type**: "Hot Water" or "Cold Water" based on surrounding color
- **Reading (m³)**: Meter reading in cubic meters (currently often "N/A" due to OCR issues)

## Requirements
- Python 3.13+
- Pillow (PIL) - Image processing
- openpyxl - Excel file creation
- numpy - Numerical operations
- pytesseract - OCR wrapper
- opencv-python (cv2) - Advanced image processing
- Tesseract-OCR - External OCR engine

## Project Structure
```
python_read_and_scan_images/
├── data/                    # Input: Place your water meter images here
├── results/                 # Output: Excel files generated here
│   └── meter_displays/      # Extracted display regions (for debugging)
├── scan_images.py          # Main script
├── water_meter_detector.py # Detection and OCR module
└── requirements.txt        # Python dependencies
```
