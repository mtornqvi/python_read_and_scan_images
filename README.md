# python_read_and_scan_images
Using Python, read images, scan information and save the information in Excel file

## Description
This program scans JPG images from the `data` folder, extracts EXIF metadata (specifically the date and time when each image was taken), and creates an Excel spreadsheet in the `results` folder.

## Features
- Scans all JPG images from the `data` folder
- Extracts date and time taken from EXIF metadata
- Creates an Excel file with:
  - Column 1: File name
  - Column 2: Date and time when the image was taken
- Output file name includes a timestamp

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Place your JPG images in the `data` folder
2. Run the script:
```bash
python scan_images.py
```
3. Find the generated Excel file in the `results` folder

## Example Output
The program will create an Excel file named like `image_metadata_20260215_143025.xlsx` containing:
- File names of all JPG images
- Date and time each image was taken (from EXIF data)

## Requirements
- Python 3.6+
- Pillow (PIL)
- openpyxl
