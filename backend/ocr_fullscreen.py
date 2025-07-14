

import pytesseract
import pyperclip
import os
from PIL import ImageGrab
import win32gui
import win32ui
import win32con
import win32api
from PIL import Image
import threading
import time
import hashlib

from ocrstore import OcrStore

# Configure Tesseract path for Windows
tesseract_paths = [
	r'C:\Program Files\Tesseract-OCR\tesseract.exe',
	r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
	r'C:\Users\{}\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'.format(os.getenv('USERNAME'))
]

v_OcrStore = OcrStore()

for path in tesseract_paths:
	if os.path.exists(path):
		pytesseract.pytesseract.tesseract_cmd = path
		break
	else:
		pass


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
	This version is enhanced for multi-monitor support.
	"""
	hwnd = find_window_by_title(window_title)
	if not hwnd:
		return None

	# Bring the window to the foreground. This can sometimes help with capture issues.
	# Note: This can be intrusive if you are doing other things.
	# Uncomment the following line if you still have issues.
	# win32gui.SetForegroundWindow(hwnd)
	# time.sleep(0.1) # Give a moment for the window to activate

	# Check if window is minimized
	placement = win32gui.GetWindowPlacement(hwnd)
	if placement[1] == win32con.SW_SHOWMINIMIZED:
		return None

	# Get window rectangle
	rect = win32gui.GetWindowRect(hwnd)
	x, y, x1, y1 = rect
	width = x1 - x
	height = y1 - y

	if width <= 0 or height <= 0:
		return None

	# --- Method 1: Try PrintWindow first ---
	# This is often reliable if the window supports it.
	try:
		hwndDC = win32gui.GetWindowDC(hwnd)
		mfcDC = win32ui.CreateDCFromHandle(hwndDC)
		saveDC = mfcDC.CreateCompatibleDC()

		saveBitMap = win32ui.CreateBitmap()
		saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
		saveDC.SelectObject(saveBitMap)

		# PW_RENDERFULLCONTENT (2) is often better than default. Let's use 2.
		# It's more thorough than the 3 you had, which isn't a standard flag.
		# The flags are 0=default, 1=PW_CLIENTONLY, 2=PW_RENDERFULLCONTENT
		result = win32gui.PrintWindow(hwnd, saveDC.GetSafeHdc(), 2)
		
		if result == 1:
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
		else:
			# Cleanup before trying next method
			win32gui.DeleteObject(saveBitMap.GetHandle())
			saveDC.DeleteDC()
			mfcDC.DeleteDC()
			win32gui.ReleaseDC(hwnd, hwndDC)
			
	except Exception as e:
		pass

	# --- Method 2: Robust ImageGrab (all_screens=True) Fallback ---
	# This is the most reliable method for multi-monitor setups when PrintWindow fails.
	try:
		
		# Get the coordinates of the entire virtual screen
		v_screen_left = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
		v_screen_top = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)
		
		# Capture the entire virtual screen
		full_screenshot = ImageGrab.grab(all_screens=True)

		# The 'rect' from GetWindowRect is in virtual screen coordinates.
		# We need to translate them to be relative to the full_screenshot image.
		crop_left = x - v_screen_left
		crop_top = y - v_screen_top
		crop_right = x1 - v_screen_left
		crop_bottom = y1 - v_screen_top

		# Crop the image to the window's bounding box
		img = full_screenshot.crop((crop_left, crop_top, crop_right, crop_bottom))

		return img
	except Exception as e:
		pass


	# --- Method 3: BitBlt (Last Resort) ---
	# This is the least reliable, especially for off-screen or occluded windows.
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

		win32gui.DeleteObject(saveBitMap.GetHandle())
		saveDC.DeleteDC()
		mfcDC.DeleteDC()
		win32gui.ReleaseDC(hwnd, hwndDC)

		return img
	except Exception as e2:
		return None

def capture_and_ocr_window(window_title):
	"""
	Capture a specific window and perform OCR on it.
	Returns the extracted text and copies it to clipboard.
	"""
	import time
	img = capture_window_by_title(window_title)
	if not img:
		return None

	# Measure OCR time
	start_time = time.time()
	text = pytesseract.image_to_string(img)
	elapsed = time.time() - start_time

	# Copy the recognized text to clipboard
	pyperclip.copy(text)

	return text

def get_image_hash(img):
	"""
	Calculate hash of an image for comparison.
	"""
	if img is None:
		return None
	# Convert to bytes for hashing
	img_bytes = img.tobytes()
	return hashlib.md5(img_bytes).hexdigest()

def periodic_caption_capture():
	"""
	Thread function that captures caption windows every 500ms.
	Performs OCR only when the image changes.
	"""
	last_hash = None
	
	while True:
		try:
			# Check for caption windows in priority order
			google_caption_window = find_window_by_title("Live Caption")
			windows_caption_window = find_window_by_title("Live Captions")
			
			target_window = None
			if google_caption_window:
				target_window = "Live Caption"
			elif windows_caption_window:
				target_window = "Live Captions"
			
			if target_window:
				# Capture the window
				img = capture_window_by_title(target_window)
				if img:
					# Calculate hash of current image
					current_hash = get_image_hash(img)
					
					# Only perform OCR if image has changed
					if current_hash != last_hash:
						
						# Measure OCR time
						start_time = time.time()
						text = pytesseract.image_to_string(img)
						elapsed = time.time() - start_time
						
						# Print the result
						if text.strip():
							# Copy to clipboard
							pyperclip.copy(text)
							v_OcrStore.add_ocr_data(text.strip())
							print(text)
							print(v_OcrStore.get_ocr_data())
						else:
							pass

						last_hash = current_hash
			else:
				# No caption window found, reset hash
				last_hash = None
		
		except Exception as e:
			pass

		# Wait 500ms before next capture
		time.sleep(0.5)

if __name__ == "__main__":
	import sys

	# Start the periodic capture thread
	capture_thread = threading.Thread(target=periodic_caption_capture, daemon=True)
	capture_thread.start()
	
	print("Starting periodic caption capture (500ms intervals)...")
	print("Press Ctrl+C to stop")
	
	try:
		# Keep the main thread alive
		while True:
			time.sleep(1)
	except KeyboardInterrupt:
		print("\nStopping caption capture...")
		sys.exit(0)
