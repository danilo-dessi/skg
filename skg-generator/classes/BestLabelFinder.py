from gensim.models.keyedvectors import KeyedVectors
from scipy import spatial
import datetime
import numpy as np
import collections
import operator
import urllib

class BestLabelFinder:
	def __init__(self, inputTexts, entitiesCleaned, relationsCleaned):
		self.relations = relationsCleaned
		self.entities = entitiesCleaned
		self.texts = inputTexts
		self.cso_triples = None
		self.cso_map = None
		self.triples = None


	def load_cso_triples_related_equivalent(self):
		triples = []
		with open('resources/CSO.3.1.csv', 'r', encoding="utf-8") as f:
			lines = f.readlines()
			for line in lines:

				try:
					(s,p,o) = tuple(line.strip().split(','))
					(s,p,o) = (urllib.parse.unquote(s[1:-1]), urllib.parse.unquote(p[1:-1]), urllib.parse.unquote(o[1:-1]))
					if "<http://cso.kmi.open.ac.uk/schema/cso#relatedEquivalent>" == p:
						triples += [(s,p,o)]
				except Exception as e:
					pass
		
		self.cso_triples = triples

	def build_cso_map(self):

		self.load_cso_triples_related_equivalent()
		
		self.cso_map = {}
		cso_topics = set()

		for (s,p,o) in self.cso_triples:
			sub = s.split('/')[-1] # last part 
			sub = sub[:-1] 		   # '>' remotion
			obj = o.split('/')[-1] # last part 
			obj = obj[:-1] 		   # '>' remotion
			cso_topics.add(sub)
			cso_topics.add(obj)


		for topic in cso_topics:

			if topic not in self.cso_map:
				equivalent_set = []
				for (s,p,o) in self.cso_triples:
			
					if "<https://cso.kmi.open.ac.uk/topics/" + topic + ">" == s:

						obj = o.split('/')[-1] # last part 
						obj = obj[:-1] 		   # '>' remotion
						equivalent_set += [obj]

				equivalent_set += [topic]
				equivalent_set = sorted(equivalent_set, key=len, reverse=True)
				equivalent_set = [e.replace('_', ' ') for e in  equivalent_set]

				for i in range(len(equivalent_set)): 
					self.cso_map[equivalent_set[i]] = equivalent_set[0]

		#for k in sorted(self.cso_map.keys()):
		#	print(k,'->', self.cso_map[k])

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


	def run(self):

			self.build_cso_map()
			model = KeyedVectors.load_word2vec_format('resources/9M[300-5]_skip_gram.bin', binary=True)
			so2verbs = {}
			so2luanyi = {}
			so2openie_verbs = {}
			
			so2texts_openie = {}
			so2texts_luanyi = {}
			so2texts_verbs = {}

			data = []
			triples = []

			for paper_number in range(len(self.relations)):
				for sentence_number in range(len(self.relations[paper_number])):
					relations = self.relations[paper_number][sentence_number]

					for (sub,p,obj) in relations:

						#solving datum issue
						if sub.endswith('datum'):
							sub = sub.replace('datum', 'data')

						if obj.endswith('datum'):
							obj = obj.replace('datum', 'data')

						# map to possible longest equal entity using cso
						if sub in self.cso_map:
							print(s,'->', self.cso_map[sub]) 
							s = self.cso_map[sub]

						else:
							s = sub

						if obj in self.cso_map:
							o = self.cso_map[obj]
						else:
							o = obj


						abstract_string = ' '.join(self.texts[paper_number])
						print((s,p,o))
						print(self.texts[paper_number][sentence_number])
						print(abstract_string,'\n')

						if p.startswith('openie-'):
							if (s,o) not in so2openie_verbs:
								so2openie_verbs[(s,o)] = []
							so2openie_verbs[(s,o)] += [p[7:]]

							if (s,o) not in so2texts_openie:
								so2texts_openie[(s,o)] = [abstract_string]
							else:
								so2texts_openie[(s,o)] += [abstract_string]

						elif p.startswith('luanyi-'):
							if (s,o) not in so2luanyi:
								so2luanyi[(s,o)] = []
							so2luanyi[(s,o)] += [p[7:]]

							if (s,o) not in so2texts_luanyi:
								so2texts_luanyi[(s,o)] = [abstract_string]
							else:
								so2texts_luanyi[(s,o)] += [abstract_string]

						elif p.startswith('verb_window-'):
							if (s,o) not in so2verbs:
								so2verbs[(s,o)] = []
							so2verbs[(s,o)] += [p[12:]]

							if (s,o) not in so2texts_verbs:
								so2texts_verbs[(s,o)] = [abstract_string]
							else:
								so2texts_verbs[(s,o)] += [abstract_string]

			for (s,o) in so2verbs:
				verbs = so2verbs[(s,o)]
				labels = self.flatWordsOnAverage(verbs, model)			
				best_label = labels[0]
				support = len(verbs)
				abstracts = so2texts_verbs[(s,o)]
				triples += [(s, best_label, o, 'heuristic', support, abstracts)]


			for (s,o) in so2openie_verbs:
				verbs = so2openie_verbs[(s,o)]
				labels = self.flatWordsOnAverage(verbs, model)			
				best_label = labels[0]
				support = len(verbs)
				abstracts = so2texts_openie[(s,o)]
				triples += [(s, best_label, o, 'openie', support, abstracts)]

			for (s,o) in so2luanyi:
				labels = so2luanyi[(s,o)]
				support = len(labels)
				counter = collections.Counter(labels)
				frequencies = sorted(counter.items(), key=operator.itemgetter(1), reverse=True)
				most_frequent_label = frequencies[0][0]
				abstracts = so2texts_luanyi[(s,o)]
				triples += [(s, most_frequent_label, o, 'luanyi', support, abstracts)]

			
			triples = [(s, label, o, source, support, tuple(abstracts)) for (s, label, o, source, support, abstracts) in triples]
			self.triples = triples



	def get_triples(self):
		return self.triples
















