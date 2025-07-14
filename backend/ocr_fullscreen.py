

import pytesseract
import pyperclip
import os
import sys
import platform

try:
    from PIL import ImageGrab
except ImportError:
    ImageGrab = None
from PIL import Image
import subprocess

# Configure Tesseract path for Windows
if platform.system() == 'Windows':
    # Common Tesseract installation paths on Windows
    tesseract_paths = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        r'C:\Users\{}\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'.format(os.getenv('USERNAME'))
    ]
    
    for path in tesseract_paths:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            break
    else:
        print("Warning: Tesseract not found in common locations. Please install Tesseract OCR or add it to your PATH.")


def capture_and_ocr_fullscreen():
    img = None
    # Use appropriate temp directory for the platform
    if platform.system() == 'Windows':
        temp_dir = os.environ.get('TEMP', os.environ.get('TMP', 'C:\\temp'))
        screenshot_path = os.path.join(temp_dir, 'ocr_fullscreen_screenshot.png')
        xwd_path = os.path.join(temp_dir, 'ocr_fullscreen.xwd')
    else:
        screenshot_path = '/tmp/ocr_fullscreen_screenshot.png'
        xwd_path = '/tmp/ocr_fullscreen.xwd'
    
    # Try ImageGrab (works on Windows and some Linux/macOS with GUI)
    if ImageGrab is not None:
        try:
            img = ImageGrab.grab()
        except Exception:
            img = None
    # Try scrot if ImageGrab failed and on Linux
    if img is None and platform.system() == 'Linux':
        try:
            subprocess.run(['scrot', screenshot_path], check=True)
            img = Image.open(screenshot_path)
        except Exception:
            img = None
    # Try xwd (X Window Dump) as a last resort on Linux
    if img is None and platform.system() == 'Linux':
        try:
            subprocess.run(['xwd', '-root', '-out', xwd_path], check=True)
            subprocess.run(['convert', xwd_path, screenshot_path], check=True)
            img = Image.open(screenshot_path)
        except Exception:
            img = None
    if img is None:
        raise RuntimeError('Failed to capture the screen. No supported method found. Ensure you are running in a desktop environment or try on Windows.')
    # Perform OCR using pytesseract
    text = pytesseract.image_to_string(img)
    # Copy the recognized text to clipboard
    pyperclip.copy(text)
    # Clean up the screenshot file if it was created
    if os.path.exists(screenshot_path):
        os.remove(screenshot_path)
    if os.path.exists(xwd_path):
        os.remove(xwd_path)
    return text

if __name__ == "__main__":
    result = capture_and_ocr_fullscreen()
    print("Recognized text copied to clipboard:")
    print(result)
