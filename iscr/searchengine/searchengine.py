from collections import defaultdict
import os
from operator import itemgetter
import sys
import time
"""
from pathos.pools import ThreadPool
"""
from .metrics import normalize, cross_entropy
from ..utils import load_from_pickle


class SearchEngine(object):
	def __init__(self, lex_pickle, index_pickle, build_wordcount=False):
		# Use this if input is text
		print("[SearchEngine] Loading lex from {}".format(lex_pickle))
		self.lex_dict = load_from_pickle(lex_pickle)

		print("[SearchEngine] Loading index from {}".format(index_pickle))
		self.indices = load_from_pickle(index_pickle)

		self.docnames = self.indices['doclengs'].keys()

		self.pool = ThreadPool(10)

		self.result = None

	def refresh_results(self):
		self.result = defaultdict(float)
		for docname in self.docnames:
			self.result[docname] = 0.

	def retrieve(self, query, negquery=None):
		"""
			Returns a list of tuples [(docname, score),...]
			For MAP, every docname has to exist
		"""
		self.refresh_results()

		self._calculate_document_scores(query, entropy_weight=1.)
		if negquery is not None:
			self._calculate_document_scores(negquery, entropy_weight=-0.1)

		sorted_ret = sorted(self.result.items(),
							key=lambda x: x[1], reverse=True)
		return sorted_ret

	def _calculate_document_scores(self, query, entropy_weight=1.):
		# Query
		for wordID, word_prob in query.items():
			# Check if query word intersects with documents
			if wordID not in self.indices['background']:
				continue

			# Recored scored documents for this word
			word_background_prob = self.indices['background'][wordID]
			word_inverted_index = self.indices['inverted_index'][wordID]

			# Iterate through every document
			for docID in self.docnames:
				# Get doc prob if in inverted_index, else set to 0.
				docprob = word_inverted_index.get(docID, 0.)

				doclength = self.indices['doclengs'][ docID ]

				smoothed_docprob = smooth_docprob(
					docprob, doclength, word_background_prob)

				weighted_entropy = entropy_weight * \
					cross_entropy(word_prob, smoothed_docprob)
				# Add to result
				self.result[docID] += weighted_entropy
	"""
	def _calculate_document_scores_pool(self, query, entropy_weight=1.):

		# Query
		def docprob_generator(word_prob, word_background_prob, word_inverted_index):
			for docname in self.docnames:
				# Get doc prob if in inverted_index, else set to 0.
				docprob = word_inverted_index.get(docname, 0.)

				doclength = self.indices['doclengs'][ docname ]

				yield docname, word_prob, docprob, doclength, word_background_prob

		def docscore_job(param):
			docname, word_prob, docprob, doclength, word_background_prob = param
			# Get doc prob if in inverted_index, else set to 0.
			docprob = word_inverted_index.get(docname, 0.)

			doclength = self.indices['doclengs'][ docname ]

			smoothed_docprob = smooth_docprob(
				docprob, doclength, word_background_prob)

			weighted_entropy = entropy_weight * \
				cross_entropy(word_prob, smoothed_docprob)
			return docname, weighted_entropy


		for wordID, word_prob in query.items():
			# Check if query word intersects with documents
			if wordID not in self.indices['background']:
				continue

			# Recored scored documents for this word
			word_background_prob = self.indices['background'][wordID]
			word_inverted_index = self.indices['inverted_index'][wordID]

			scores = self.pool.map(docscore_job, docprob_generator(word_prob, word_background_prob, word_inverted_index))

			for docname, weighted_entropy in scores:
				self.result[ docname ] += weighted_entropy
	"""

def smooth_docprob(docprob, doclength, word_background_prob, alpha=1000):
	# Get smoothing weight
	alpha_d = doclength / (doclength + alpha)
	# Smooth by interpolation with background probability
	smoothed_docprob = (1 - alpha_d) * word_background_prob + alpha_d * docprob
	return smoothed_docprob


if __name__ == "__main__":
	pass
