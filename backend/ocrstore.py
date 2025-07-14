"""

This class is for handling and management string data from OCR operations.

"""

class OcrStore:
	def __init__(self):
		self.ocr_data = []
		self.ocr_sentences = {}
	
	def add_ocr_data(self, ocr_text):
		"""
		Split ocr_text by '\n' and store it to ocr_data.

		Storing work is like merging 
		"""
		if ocr_text is None:
			return

		new_lines = ocr_text.split('\n')
		# Remove all '' empty lines in new_lines array

		new_lines = [line for line in new_lines if line.strip()]

		for i in range(len(self.ocr_data) - 1, -1, -1):
			if self.ocr_data[i] == new_lines[0]:
				k = 1
				j = i + 1
				# Overwrite existing lines
				while j < len(self.ocr_data) and k < len(new_lines):
					self.ocr_data[j] = new_lines[k]
					j += 1
					k += 1
				# Append remaining lines
				while k < len(new_lines):
					self.ocr_data.append(new_lines[k])
					k += 1
				return
		self.ocr_data.extend(new_lines)
	def get_ocr_data(self):
		"""
		Return the stored OCR data.
		"""
		return self.ocr_data