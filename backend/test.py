def is_similar(text1, text2):
	"""
	Check if two strings are similar enough to be considered the same.
	We compare words instead of characters, ignoring punctuation and case differences.
	Uses word-level edit distance (Levenshtein distance) with a threshold of 0.8.
	"""
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
	
	print(f"Comparing words: {words1}")
	print(f"            and: {words2}")
	print(f"Edit distance: {edit_dist}, Max length: {max_length}")
	print(f"Similarity ratio: {similarity:.3f}")
	
	return similarity >= 0.8


text1 = "The quick brown fox jumps over the lazy dog."
text2 = "The quick brown fox jumped over the lazy dog."

if __name__ == "__main__":
	print(is_similar(text1, text2))  # Should return True or False based on similarity
