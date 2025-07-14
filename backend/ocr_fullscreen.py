

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


def capture_and_ocr_fullscreen():
    img = None
    screenshot_path = '/tmp/ocr_fullscreen_screenshot.png'
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
            subprocess.run(['xwd', '-root', '-out', '/tmp/ocr_fullscreen.xwd'], check=True)
            subprocess.run(['convert', '/tmp/ocr_fullscreen.xwd', screenshot_path], check=True)
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
    if os.path.exists('/tmp/ocr_fullscreen.xwd'):
        os.remove('/tmp/ocr_fullscreen.xwd')
    return text

if __name__ == "__main__":
    result = capture_and_ocr_fullscreen()
    print("Recognized text copied to clipboard:")
    print(result)
