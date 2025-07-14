

import pytesseract
import pyperclip
import os
from PIL import ImageGrab
import win32gui
import win32ui
import win32con
from PIL import Image

# Configure Tesseract path for Windows
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


def list_all_windows():
	"""
	List all visible windows with their titles.
	Useful for finding the exact window name to capture.
	"""
	def enum_windows_callback(hwnd, windows):
		if win32gui.IsWindowVisible(hwnd):
			title = win32gui.GetWindowText(hwnd)
			if title.strip():  # Only show windows with titles
				windows.append(title)
		return True
	
	windows = []
	win32gui.EnumWindows(enum_windows_callback, windows)
	
	print("Available windows:")
	for i, title in enumerate(windows, 1):
		print(f"{i}: {title}")
	
	return windows


def find_window_by_title(window_title):
	"""
	Find a window by its title (or partial title).
	Returns the window handle (hwnd) if found, None otherwise.
	"""
	def enum_windows_callback(hwnd, windows):
		if win32gui.IsWindowVisible(hwnd):
			title = win32gui.GetWindowText(hwnd)
			if window_title.lower() in title.lower():
				windows.append((hwnd, title))
		return True
	
	windows = []
	win32gui.EnumWindows(enum_windows_callback, windows)
	
	if windows:
		# If multiple windows found, return the first one
		return windows[0][0]  # Return hwnd
	return None


def capture_window_by_title(window_title):
	"""
	Capture a specific window by its title.
	Returns PIL Image of the window or None if not found.
	"""
	hwnd = find_window_by_title(window_title)
	if not hwnd:
		return None
	
	# Get window rectangle
	rect = win32gui.GetWindowRect(hwnd)
	x, y, x1, y1 = rect
	width = x1 - x
	height = y1 - y
	
	if width <= 0 or height <= 0:
		return None
	
	try:
		# Use ImageGrab with the window region - this works best for most windows
		img = ImageGrab.grab(bbox=(x, y, x1, y1))
		return img
		
	except Exception as e:
		# Fallback to Win32 API approach if ImageGrab fails
		try:
			hwndDC = win32gui.GetWindowDC(hwnd)
			mfcDC = win32ui.CreateDCFromHandle(hwndDC)
			saveDC = mfcDC.CreateCompatibleDC()
			
			saveBitMap = win32ui.CreateBitmap()
			saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
			saveDC.SelectObject(saveBitMap)
			
			saveDC.BitBlt((0, 0), (width, height), mfcDC, (0, 0), win32con.SRCCOPY)
			
			bmpinfo = saveBitMap.GetInfo()
			bmpstr = saveBitMap.GetBitmapBits(True)
			img = Image.frombuffer(
				'RGB',
				(bmpinfo['bmWidth'], bmpinfo['bmHeight']),
				bmpstr, 'raw', 'BGRX', 0, 1
			)
			
			# Cleanup
			win32gui.DeleteObject(saveBitMap.GetHandle())
			saveDC.DeleteDC()
			mfcDC.DeleteDC()
			win32gui.ReleaseDC(hwnd, hwndDC)
			
			return img
			
		except Exception:
			return None


def capture_and_ocr_window(window_title):
	"""
	Capture a specific window and perform OCR on it.
	Returns the extracted text and copies it to clipboard.
	"""
	img = capture_window_by_title(window_title)
	if not img:
		return None
	
	# Perform OCR directly on the image in memory
	text = pytesseract.image_to_string(img)
	
	# Copy the recognized text to clipboard
	pyperclip.copy(text)
	
	return text

if __name__ == "__main__":
	import sys

	google_caption_window = find_window_by_title("Live Caption")
	windows_caption_window = find_window_by_title("Live Captions")

	print("Available windows:")

	result = ""
	if google_caption_window:
		result = capture_and_ocr_window("Live Caption")
	elif windows_caption_window:
		result = capture_and_ocr_window("Live Captions")

	if result is not None:
		print(f"OCR result from 'Live Captions' window copied to clipboard:")
		if result.strip():
			print(result)
		else:
			print("(No text detected in the window)")
	else:
		print(f"Window containing 'Live Captions' not found.")
		print("Use --list to see all available windows.")
