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
import keyboard

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
							v_OcrStore.add_ocr_data(text.strip())
							
							# looping print all ocr store data line by line

							v_OcrStore.rearrange_sentences()
       
							# Copy all sentences(not ocrdata) to clipboard
							pyperclip.copy("\n".join(v_OcrStore.get_ocr_sentences()))
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

def perform_paste_sequence(sentences_to_paste):
	"""
	Perform the key sequence: Ctrl+A, Delete, Ctrl+V
	This will select all text, delete it, and paste the specified sentences.
	"""
	try:
		# Copy the sentences to clipboard first
		if sentences_to_paste:
			pyperclip.copy("\n".join(sentences_to_paste))
		else:
			pyperclip.copy("")
		
		# Small delay to ensure the hotkey is released
		time.sleep(0.1)
		
		# Ctrl+A (Select All)
		keyboard.send('ctrl+a')
		time.sleep(0.05)  # Small delay between operations
		
		# Delete key
		keyboard.send('delete')
		time.sleep(0.05)
		
		# Ctrl+V (Paste)
		keyboard.send('ctrl+v')
		
	except Exception as e:
		pass

def get_last_n_sentences(n):
	"""
	Get the last n sentences from the OCR store.
	"""
	sentences = v_OcrStore.get_ocr_sentences()
	if not sentences:
		return []
	return sentences[-n:] if len(sentences) >= n else sentences

def clear_all_data():
	"""
	Clear all OCR data and sentences.
	"""
	global v_OcrStore
	v_OcrStore.ocr_data = []
	v_OcrStore.ocr_sentences = []

# Global variable to track decimal key presses
decimal_press_count = 0

def reset_decimal_counter():
	"""Reset the decimal press counter when any other key is pressed"""
	global decimal_press_count
	decimal_press_count = 0

def setup_hotkeys():
	"""
	Set up hotkey listeners for numpad keys.
	- Numpad 1-9: Copy last 2,4,6,8...18 sentences respectively
	- Numpad 0: Copy all sentences
	- Numpad . (double press): Clear all data
	"""
	
	def on_numpad_1():
		reset_decimal_counter()
		sentences = get_last_n_sentences(2)
		perform_paste_sequence(sentences)
	
	def on_numpad_2():
		reset_decimal_counter()
		sentences = get_last_n_sentences(4)
		perform_paste_sequence(sentences)
	
	def on_numpad_3():
		reset_decimal_counter()
		sentences = get_last_n_sentences(6)
		perform_paste_sequence(sentences)
	
	def on_numpad_4():
		reset_decimal_counter()
		sentences = get_last_n_sentences(8)
		perform_paste_sequence(sentences)
	
	def on_numpad_5():
		reset_decimal_counter()
		sentences = get_last_n_sentences(10)
		perform_paste_sequence(sentences)
	
	def on_numpad_6():
		reset_decimal_counter()
		sentences = get_last_n_sentences(12)
		perform_paste_sequence(sentences)
	
	def on_numpad_7():
		reset_decimal_counter()
		sentences = get_last_n_sentences(14)
		perform_paste_sequence(sentences)
	
	def on_numpad_8():
		reset_decimal_counter()
		sentences = get_last_n_sentences(16)
		perform_paste_sequence(sentences)
	
	def on_numpad_9():
		reset_decimal_counter()
		sentences = get_last_n_sentences(18)
		perform_paste_sequence(sentences)
	
	def on_numpad_0():
		reset_decimal_counter()
		sentences = v_OcrStore.get_ocr_sentences()
		perform_paste_sequence(sentences)
	
	def on_numpad_decimal():
		global decimal_press_count, decimal_last_press_time
		
		decimal_press_count += 1
		
		if decimal_press_count == 1:
			pass
		elif decimal_press_count == 2:
			clear_all_data()
			decimal_press_count = 0  # Reset counter after clearing
		else:
			# This shouldn't happen with sequential presses, but just in case
			decimal_press_count = 0
	
	# Set up hotkeys with suppression (suppress=True prevents the key from being typed)
	hotkey_mappings = [
		('num 1', on_numpad_1),
		('num 2', on_numpad_2),
		('num 3', on_numpad_3),
		('num 4', on_numpad_4),
		('num 5', on_numpad_5),
		('num 6', on_numpad_6),
		('num 7', on_numpad_7),
		('num 8', on_numpad_8),
		('num 9', on_numpad_9),
		('num 0', on_numpad_0),
	]
	
	# Try different possible names for numpad decimal
	decimal_key_names = ['num .', 'num del', 'decimal', 'num decimal', 'keypad .', 'kp_decimal']
	
	for key, callback in hotkey_mappings:
		try:
			keyboard.add_hotkey(key, callback, suppress=True)
		except Exception as e:
			pass

	# Try to register numpad decimal with different names
	decimal_registered = False
	for key_name in decimal_key_names:
		try:
			keyboard.add_hotkey(key_name, on_numpad_decimal, suppress=True)
			decimal_registered = True
			break
		except Exception as e:
			pass

	if not decimal_registered:
		# Alternative approach using keyboard hook
		try:
			def on_key_event(event):
				if event.event_type == keyboard.KEY_DOWN:
					if event.name in ['decimal', '.', 'num .', 'kp_decimal']:
						on_numpad_decimal()
						return False  # Suppress the key
				return True
			
			keyboard.hook(on_key_event)
		except Exception as e:
			pass

if __name__ == "__main__":
	import sys

	# Start the periodic capture thread
	capture_thread = threading.Thread(target=periodic_caption_capture, daemon=True)
	capture_thread.start()
	
	# Set up hotkeys
	setup_hotkeys()
	
	try:
		# Keep the main thread alive
		while True:
			time.sleep(1)
	except KeyboardInterrupt:
		sys.exit(0)
