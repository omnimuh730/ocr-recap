

import pytesseract
import pyperclip
import os
from PIL import ImageGrab
import win32gui
import win32ui
import win32con
import win32api
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
	This version is enhanced for multi-monitor support.
	"""
	hwnd = find_window_by_title(window_title)
	if not hwnd:
		print(f"Window containing '{window_title}' not found.")
		return None

	# Bring the window to the foreground. This can sometimes help with capture issues.
	# Note: This can be intrusive if you are doing other things.
	# Uncomment the following line if you still have issues.
	# win32gui.SetForegroundWindow(hwnd)
	# time.sleep(0.1) # Give a moment for the window to activate

	# Check if window is minimized
	placement = win32gui.GetWindowPlacement(hwnd)
	if placement[1] == win32con.SW_SHOWMINIMIZED:
		print(f"Window '{window_title}' is minimized. Please restore it and try again.")
		return None

	# Get window rectangle
	rect = win32gui.GetWindowRect(hwnd)
	x, y, x1, y1 = rect
	width = x1 - x
	height = y1 - y
	print(f"Window '{window_title}' rect: {rect} (width={width}, height={height})")

	if width <= 0 or height <= 0:
		print(f"Window '{window_title}' has invalid size (maybe hidden or closed).")
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
			
			print(f"Successfully captured using PrintWindow")
			return img
		else:
			print("PrintWindow failed (result=0), trying robust ImageGrab fallback.")
			# Cleanup before trying next method
			win32gui.DeleteObject(saveBitMap.GetHandle())
			saveDC.DeleteDC()
			mfcDC.DeleteDC()
			win32gui.ReleaseDC(hwnd, hwndDC)
			
	except Exception as e:
		print(f"PrintWindow method raised an exception: {e}. Trying robust ImageGrab fallback.")

	# --- Method 2: Robust ImageGrab (all_screens=True) Fallback ---
	# This is the most reliable method for multi-monitor setups when PrintWindow fails.
	try:
		print("Trying robust ImageGrab (all_screens) method...")
		
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

		print(f"ImageGrab (all_screens) captured image size: {img.size}")
		return img
	except Exception as e:
		print(f"Robust ImageGrab (all_screens) failed: {e}. Trying BitBlt as a last resort.")


	# --- Method 3: BitBlt (Last Resort) ---
	# This is the least reliable, especially for off-screen or occluded windows.
	try:
		print("Trying BitBlt method...")
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

		print(f"BitBlt captured image size: {img.size}")
		return img
	except Exception as e2:
		print(f"BitBlt method also failed: {e2}")
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
	print(f"OCR took {elapsed:.3f} seconds.")

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
