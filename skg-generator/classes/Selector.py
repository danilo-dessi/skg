import pandas as pd 
import urllib
from gensim.models.keyedvectors import KeyedVectors
from sklearn.neural_network import MLPClassifier as mlp
from gensim.models import Word2Vec
import numpy as np
from scipy import spatial
from nltk.corpus import wordnet as wn
import nltk
import os


class Selector:

	def __init__(self, triples):
		self.input_triples = triples
		self.out_triples = None
		self.vectors_model = 'resources/300model.bin'
		self.trust_th = 10
		self.discarded_triples = None


	def clean_for_embeddings(self, e_text):
		chs = ['(', ')', '-']
		for c in chs:
			e_text = e_text.replace(c, ' ')
		tokens = nltk.word_tokenize(e_text)
		e_text = ' '.join(tokens)
		return e_text


	def wup_sim(self, v1, v2):
		vs1 = wn.synsets(v1, pos=wn.VERB)
		vs2 = wn.synsets(v2, pos=wn.VERB)
		max_sim = 0

		for s1 in vs1:
			for s2 in vs2:
				sim = s1.wup_similarity(s2)
				if sim > max_sim:
					max_sim = sim
		return max_sim

	def get_classifier(self, trusted_triples):
		model = KeyedVectors.load_word2vec_format(self.vectors_model, binary=True)
		X = []
		y = []
		for (s,p,o,suorce,support) in trusted_triples:
			skey = self.clean_for_embeddings(s).replace(' ', '_')  
			okey = self.clean_for_embeddings(o).replace(' ', '_') 

			if skey in model and okey in model:
				vec = np.concatenate((model[skey], model[okey]), axis=None)
				X += [vec]
				y += [p]

		X = np.array(X)
		clf = mlp(hidden_layer_sizes=(100,))
		clf.fit(X, y)
		return clf



	def get_consistent(self, clf, untrusted_triples):
		model = KeyedVectors.load_word2vec_format(self.vectors_model, binary=True)
		
		consistent = []
		for (s,verb,o,suorce,support) in untrusted_triples:
			skey_test = self.clean_for_embeddings(s).replace(' ', '_')  
			okey_test = self.clean_for_embeddings(o).replace(' ', '_') 

			try:
				test = np.asarray([np.concatenate((model[skey_test], model[okey_test]), axis=None)])
				pred = clf.predict(test)[0]


				if pred == verb:
					consistent += [(s,verb,o,suorce,support)]
				else:
					wverb = model[verb]
					wpred = model[pred]
					sim = 1 - spatial.distance.cosine(wverb, wpred)
					sim_wn = wup_sim(verb, pred)
					if (sim + sim_wn) / 2 >= 0.5:
						consistent += [(s,verb,o,suorce,support)]
						print((s,verb,o,suorce,support), pred)
			except Exception as e:
				continue

		return consistent


	def build_embeddings(self, keys, emb_size):
		text = None
		with open('resources/semantic_web_28k_abstracts.txt', 'r') as f:
			text = f.read().lower()
			text = clean_for_embeddings(text)
		keys = sorted(set(keys), key=len, reverse=True) 

		for e in keys:
			e_tmp = clean_for_embeddings(e)
			if e_tmp in text:
				text = text.replace(e_tmp, e_tmp.replace(' ', '_'))

		sentences = nltk.sent_tokenize(text)
		sentences = [nltk.word_tokenize(s) for s in sentences]
		model = Word2Vec(sentences=sentences, min_count=1, size=emb_size)
		model.wv.save_word2vec_format('resources/' + str(emb_size) + 'model.bin', binary=True)

	def remove_conjunction(self):
		triples = []
		for (s,p,o,source,support)  in self.input_triples:
			if p != 'conjunction':
				triples += [(s,p,o,source,support)]
		self.input_triples = triples


	def remove_equal_s_o(self):
		triples = []
		for (s,p,o,source,support)  in self.input_triples:
			if s != o:
				triples += [(s,p,o,source,support)]
		self.input_triples = triples

			

	# Subject and object can have at most 3 predicates coming from the three different methods.
	# This method chooses pnly one predicate following this order: 1. Luanyi, 2. openie, 3. heuristic
	def unique(self, triples):
		unique_triples = set()
		seen = set()

		for (s,p,o,source,support) in triples:
			if (s,o) not in seen and source == 'luanyi':
				unique_triples.add((s,p,o,source,support))
				seen.add((s,o))

		for (s,p,o,source,support) in triples:
			if (s,o) not in seen and source == 'openie':
				unique_triples.add((s,p,o,source,support))
				seen.add((s,o))

		for (s,p,o,source,support) in triples:
			if (s,o) not in seen and source == 'heuristic':
				unique_triples.add((s,p,o,source,support))
				seen.add((s,o))
		return list(unique_triples)
		


	def get_selected_triples(self):
		return self.out_triples

	def get_discarded_triples(self):
		return self.discarded_triples


	def run(self):
		trusted_triples = []
		untrusted_triples = []

		if not os.path.isfile(self.vectors_model):
			print('300model.bin does not exist -> Generation of new embeddings')
			entities = set()
			for (s,p,o,source,support)  in self.input_triples:
				entities.add(s)
				entities.add(o)	
			self.build_embeddings(entities, 300)

		self.remove_conjunction()
		self.remove_equal_s_o()

		for (s,p,o,source,support)  in self.input_triples:
			if source == 'luanyi' or source == 'openie' or support >= self.trust_th:
				trusted_triples += [(s,p,o,source,support)]
			else:
				untrusted_triples += [(s,p,o,source,support)]

		trusted_triples_for_classifier = self.unique(trusted_triples)
		print('Trusted triples:', len(trusted_triples))
		print('Untrusted triples:', len(untrusted_triples))
		clf = self.get_classifier(trusted_triples_for_classifier)
		consistent_triples = self.get_consistent(clf, untrusted_triples)

		print('Consistent triples:', len(consistent_triples))
		self.out_triples = trusted_triples + consistent_triples
		self.discarded_triples = [item for item in untrusted_triples if item not in consistent_triples]
		print('Total selected triples:', len(self.out_triples))
		print('Discarded triples:', len(self.discarded_triples))











