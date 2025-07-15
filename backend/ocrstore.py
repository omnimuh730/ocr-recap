"""

This class is for handling and management string data from OCR operations.

"""

class OcrStore:
	def __init__(self):
		self.ocr_data = []
		self.ocr_sentences = []

	def is_similar(self, text1, text2):
		if text1 is None or text2 is None:
			return False
		
		def clean_word(word):
			"""Remove punctuation and convert to lowercase"""
			import re
			return re.sub(r'[^\w]', '', word.lower())
		
		def get_clean_words(text):
			"""Split text into words and clean them"""
			words = text.split()
			return [clean_word(word) for word in words if clean_word(word)]
		
		def word_edit_distance(words1, words2):
			"""Calculate edit distance between two word sequences using dynamic programming"""
			m, n = len(words1), len(words2)
			
			# Create a matrix to store edit distances
			dp = [[0] * (n + 1) for _ in range(m + 1)]
			
			# Initialize base cases
			for i in range(m + 1):
				dp[i][0] = i  # Cost of deleting all words from words1
			for j in range(n + 1):
				dp[0][j] = j  # Cost of inserting all words from words2
			
			# Fill the matrix
			for i in range(1, m + 1):
				for j in range(1, n + 1):
					if words1[i-1] == words2[j-1]:
						dp[i][j] = dp[i-1][j-1]  # No operation needed
					else:
						dp[i][j] = 1 + min(
							dp[i-1][j],    # Delete from words1
							dp[i][j-1],    # Insert into words1
							dp[i-1][j-1]   # Replace in words1
						)
			
			return dp[m][n]
		
		words1 = get_clean_words(text1)
		words2 = get_clean_words(text2)
		
		if not words1 or not words2:
			return False
		
		if words1 == words2:
			return True
		
		# Calculate edit distance
		edit_dist = word_edit_distance(words1, words2)
		max_length = max(len(words1), len(words2))
		
		# Calculate similarity ratio
		similarity = 1 - (edit_dist / max_length)
		
		return similarity >= 0.5


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
			if self.is_similar(self.ocr_data[i], new_lines[0]) == True:
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
	def get_ocr_sentences(self):
		"""
		Return the stored OCR sentences.
		"""
		return self.ocr_sentences
	def rearrange_sentences(self):
		"""
		Rearrange sentences in ocr_data to form complete sentences.
		This modifies ocr_sentences based on ocr_data by properly splitting text into sentences.
		"""
		if not self.ocr_data:
			return
		
		# Join all lines into a single text block
		full_text = " ".join(line.strip() for line in self.ocr_data if line.strip())
		
		if not full_text:
			self.ocr_sentences = []
			return
		
		# Split into sentences using a more sophisticated approach
		self.ocr_sentences = self._split_into_sentences(full_text)
	
	def _split_into_sentences(self, text):
		"""
		Split text into sentences using a more robust approach.
		Handles multiple sentences per line and common abbreviations.
		"""
		import re
		
		# Common abbreviations that shouldn't trigger sentence breaks
		abbreviations = {
			'Mr.', 'Mrs.', 'Ms.', 'Dr.', 'Prof.', 'Sr.', 'Jr.',
			'Inc.', 'Ltd.', 'Co.', 'Corp.', 'etc.', 'vs.', 'e.g.',
			'i.e.', 'U.S.', 'U.K.', 'U.N.', 'No.', 'St.', 'Ave.',
			'Blvd.', 'Rd.', 'Dept.', 'Gov.', 'Rep.', 'Sen.'
		}
		
		# Replace abbreviations with placeholders to avoid false sentence breaks
		placeholder_map = {}
		for i, abbr in enumerate(abbreviations):
			placeholder = f"__ABBR_{i}__"
			if abbr in text:
				text = text.replace(abbr, placeholder)
				placeholder_map[placeholder] = abbr
		
		# Split on sentence-ending punctuation followed by whitespace and capital letter
		# This regex looks for:
		# - Sentence ending punctuation (. ! ?)
		# - Followed by one or more whitespace characters
		# - Followed by a capital letter or digit
		sentence_pattern = r'([.!?])\s+(?=[A-Z0-9])'
		
		# Split the text
		parts = re.split(sentence_pattern, text)
		
		sentences = []
		current_sentence = ""
		
		for i, part in enumerate(parts):
			if part in '.!?':
				# This is punctuation, add it to current sentence
				current_sentence += part
				# Add the complete sentence
				if current_sentence.strip():
					sentences.append(current_sentence.strip())
				current_sentence = ""
			else:
				# This is text content
				current_sentence += part
		
		# Add any remaining text as a sentence
		if current_sentence.strip():
			sentences.append(current_sentence.strip())
		
		# Restore abbreviations from placeholders
		for i, sentence in enumerate(sentences):
			for placeholder, abbr in placeholder_map.items():
				sentence = sentence.replace(placeholder, abbr)
			sentences[i] = sentence
		
		# Filter out empty sentences and clean up
		sentences = [s.strip() for s in sentences if s.strip()]
		
		return sentences
