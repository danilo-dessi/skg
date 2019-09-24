from gensim.models.keyedvectors import KeyedVectors
from scipy import spatial
import datetime
import numpy as np
import collections
import operator


class BestLabelFinder:
	def __init__(self, inputTexts, entitiesCleaned, relationsCleaned):
		self.relations = relationsCleaned
		self.entities = entitiesCleaned
		self.texts = inputTexts

		self.triples = None


	def flatWordsOnAverage(self, wordList, model):
		X = []
		X_i = []
		stopVerbs = ['have', 'be', 'do']
		
		for i in range(len(wordList)):
			word = wordList[i]
			if word.lower() in model and word != 'RELATE':
				X += [model[word.lower()]]
				X_i += [i]

		if len(X) > 0:
			avg = np.array(X).mean(0)

			XDistance = []
			for i in range(len(X)):
				x = X[i]
				sim = 1 - spatial.distance.cosine(x, avg)
				XDistance += [(x, wordList[X_i[i]], sim)]
				
			coeff = 0.8
			XDistanceTemp = []
			for (x, w, sim) in XDistance:
				if w in stopVerbs:
					XDistanceTemp += [(x, w, sim*0.8)]
				else:
					XDistanceTemp += [(x, w, sim)]
			XDistance  = XDistanceTemp

			mostSimilar = sorted(XDistance, key=lambda x: x[2], reverse=True)[0]
			noMap = [ w for (x, w, sim) in XDistance if sim < 0.7]
			resultingVerbs = [mostSimilar[1]] + noMap

			#list of verbs ordered considering the distance from the averaged word embedding
			return resultingVerbs 
		else:
			#in case of error a first element of the input wordList is returned by default
			return [wordList[0]]


	def make_triples(self):
			model = KeyedVectors.load_word2vec_format('resources/9M[300-5]_skip_gram.bin', binary=True)
			so2verbs = {}
			so2openie_verbs = {}
			so2luanyi = {}

			spo2sentences = {}
			spo_openie2sentences = {}
			spo_luanyi2sentences = {}

			data = []
			triples = []

			for paper_number in range(len(self.relations)):
				for sentence_number in range(len(self.relations[paper_number])):
					relations = self.relations[paper_number][sentence_number]

					for (s,p,o) in relations:
						if p.startswith('v-'):
							if (s,o) not in so2openie_verbs:
								so2openie_verbs[(s,o)] = []

							if (s,p,o) not in spo_openie2sentences:
								spo_openie2sentences[(s,p[2:],o)] = []

							so2openie_verbs[(s,o)] += [p[2:]]
							spo_openie2sentences[(s,p[2:],o)] += [self.texts[paper_number][sentence_number]]

						elif p.startswith('luanyi-'):
							if (s,o) not in so2luanyi:
								so2luanyi[(s,o)] = []

							if (s,p,o) not in spo_luanyi2sentences:
								spo_luanyi2sentences[(s,p[7:],o)] = []

							so2luanyi[(s,o)] += [p[7:]]
							spo_luanyi2sentences[(s,p[7:],o)] += [self.texts[paper_number][sentence_number]]

						else:
							if (s,o) not in so2verbs:
								so2verbs[(s,o)] = []

							if (s,p,o) not in spo2sentences:
								spo2sentences[(s,p,o)] = []

							so2verbs[(s,o)] += [p]
							spo2sentences[(s,p,o)] += [self.texts[paper_number][sentence_number]]

			for (s,o) in so2verbs:
				verbs = so2verbs[(s,o)]
				labels = self.flatWordsOnAverage(verbs, model)			
				best_label = labels[0]
				support = len(verbs)
				triples += [(s, best_label, o, 'heuristic', support)]

			for (s,o) in so2openie_verbs:
				verbs = so2openie_verbs[(s,o)]
				labels = self.flatWordsOnAverage(verbs, model)			
				best_label = labels[0]
				support = len(verbs)
				triples += [(s, best_label, o, 'openie', support)]

			for (s,o) in so2luanyi:
				labels = so2luanyi[(s,o)]
				support = len(labels)
				counter = collections.Counter(labels)
				frequencies = sorted(counter.items(), key=operator.itemgetter(1), reverse=True)
				most_frequent_label = frequencies[0][0]
				triples += [(s, most_frequent_label, o, 'luanyi', support)]

			#return triples
			self.triples = triples



	def get_triples(self):
		return self.triples



	def run(self):
		self.make_triples()















