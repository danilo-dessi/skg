from classes.EntityCleaner import EntityCleaner
from classes.RelationsDeepFinder import RelationsDeepFinder
from classes.StatisticsRefiner import StatisticsRefiner
from classes.Mapper import Mapper
from classes.Selector import Selector

import sys
import pandas as pd
import ast
import networkx as nx
import Levenshtein.StringMatcher as ls
import datetime
import nltk
import numpy as np
from gensim.models.keyedvectors import KeyedVectors
from scipy import spatial
import operator
import random
import collections


class GraphBuilder:

	def __init__(self, inputFile):
		self.inputFile = inputFile
		self.inputDataFrame = None
		self.inputEntities = None
		self.inputRelations = None
		self.inputTexts = None
		
		self.relationsRefined = None
		self.entitiesCleaned = None
		self.relationsCleaned = None
		self.entitiesEmbeddingsMap = {}
		self.entity2embedding = {}
		self.g = nx.DiGraph()
		self.validEntities = set()
		self.rel2sent = {}
		self.id2sent = None


	def loadData(self):
		self.inputDataFrame = pd.read_csv(self.inputFile)#.head(50)


	def parse(self):
		self.inputEntities = [ast.literal_eval(e) for e in self.inputDataFrame['entities_column'].tolist()]
		self.inputRelations = [ast.literal_eval(r) for r in self.inputDataFrame['relations_column'].tolist()]
		self.inputTexts = [ast.literal_eval(t) for t in self.inputDataFrame['sentences'].tolist()]

		tmp_input_texts = []
		for paper_number in range(len(self.inputTexts)):
			paper_sentences = []
			for sentence_number in range(len(self.inputTexts[paper_number])):
				sentence = self.inputTexts[paper_number][sentence_number].lower()
				paper_sentences += [sentence]
			tmp_input_texts += [paper_sentences]
		self.inputTexts = tmp_input_texts

		newInputEntities = []
		for eList in self.inputEntities:
			newEList = []
			for eSentence in eList:
				newESentence = []
				for e in eSentence:
					newESentence += [e.lower()]
				newEList += [newESentence]
			newInputEntities += [newEList]
		self.inputEntities = newInputEntities

		newInputRelations = []
		for rList in self.inputRelations:
			newRList = []
			for rSentence in rList:
				newRSentence = []
				for (s,p,o) in rSentence:
					newRSentence += [(s.lower(), p.lower(), o.lower())]
				newRList += [newRSentence]
			newInputRelations += [newRList]
		self.inputRelations = newInputRelations


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

			return resultingVerbs
		else:
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

		for paper_number in range(len(self.relationsCleaned)):
			for sentence_number in range(len(self.relationsCleaned[paper_number])):
				relations = self.relationsCleaned[paper_number][sentence_number]

				for (s,p,o) in relations:
					if p.startswith('v-'):
						if (s,o) not in so2openie_verbs:
							so2openie_verbs[(s,o)] = []

						if (s,p,o) not in spo_openie2sentences:
							spo_openie2sentences[(s,p[2:],o)] = []

						so2openie_verbs[(s,o)] += [p[2:]]
						spo_openie2sentences[(s,p[2:],o)] += [self.inputTexts[paper_number][sentence_number]]

					elif p.startswith('luanyi-'):
						if (s,o) not in so2luanyi:
							so2luanyi[(s,o)] = []

						if (s,p,o) not in spo_luanyi2sentences:
							spo_luanyi2sentences[(s,p[7:],o)] = []

						so2luanyi[(s,o)] += [p[7:]]
						spo_luanyi2sentences[(s,p[7:],o)] += [self.inputTexts[paper_number][sentence_number]]

					else:
						if (s,o) not in so2verbs:
							so2verbs[(s,o)] = []

						if (s,p,o) not in spo2sentences:
							spo2sentences[(s,p,o)] = []

						so2verbs[(s,o)] += [p]
						spo2sentences[(s,p,o)] += [self.inputTexts[paper_number][sentence_number]]

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
			triples += [(s, best_label, o, 'luanyi', support)]

		return triples

		
	def removeNoConnectedNodes(self):
		isolated_nodes = [n for n,d in self.g.degree() if d == 0]
		self.g.remove_nodes_from(isolated_nodes)

	def removeSelfEdges(self):
		self.g.remove_edges_from(self.g.selfloop_edges())

	def validate(self):
		allEntities = [] 
		for i in range(len(self.inputEntities)):
			for eList in self.inputEntities[i]:
				allEntities += [e for e in eList]

		allEntities = set(allEntities)	
		refiner = StatisticsRefiner(allEntities, self.inputEntities, self.inputRelations, 10, 15)
		self.validEntities, self.inputEntities,  self.inputRelations = refiner.validate()
		print('Entities after:', len(self.validEntities))#, len(set([e for l in self.inputEntities for e in l])))


	def relationsRefinement(self):
		refiner = RelationsDeepFinder(self.inputTexts, self.inputEntities, self.inputRelations, self.rel2sent)
		self.relationsRefined = refiner.run() 


	def cleanEntities(self):
		entityCleaner = EntityCleaner(self.inputEntities, self.relationsRefined, self.validEntities, self.rel2sent, self.id2sent)
		entityCleaner.run()

		self.relationsRefined = None
		self.entitiesCleaned = entityCleaner.getEntitiesCleaned()
		self.relationsCleaned = entityCleaner.getRelationsCleaned()


	def build_g(self, selected_triples):

		id_gen = 0
		entity2id = {}
		id2entity = {}

		#a single id to each entity
		for (s,p,o, source, support) in selected_triples:
			if s not in entity2id:
				entity2id[s] = id_gen
				id2entity[id_gen] = s
				self.g.add_node(id_gen, label=s)
				id_gen += 1
			if o not in entity2id:
				entity2id[o] = id_gen
				id2entity[id_gen] = o
				self.g.add_node(id_gen, label=o)
				id_gen += 1

		#graph generation
		for (s,p,o, source, support) in selected_triples:
			idS = entity2id[s]
			idO = entity2id[o]
			self.g.add_edge(idS, idO, label=p, support=support, source=source)

		
	def pipeline(self):

		print('# LOAD AND PARSE DATA')
		print(str(datetime.datetime.now()))
		self.loadData()
		self.parse()
		print()


		print('# ENTITIES VALIDATION')
		print(str(datetime.datetime.now()))
		self.validate()
		print()

		print('# DEEP FINDER')
		print(str(datetime.datetime.now()))
		self.relationsRefinement()
		print()
		

		print('# ENTITIES CLEANING')
		print(str(datetime.datetime.now()))
		self.cleanEntities()
		print()

		print('# TRIPLES GENERATION')
		triples = self.make_triples()
		print('Number of triples:', len(triples))

		print('# TRIPLES MAPPING')
		print(str(datetime.datetime.now()))
		m = Mapper(triples)
		m.run()
		triples = m.get_triples()
		print('Number of triples:', len(triples))

		columns_order = ['s', 'p', 'o', 'source', 'support']
		data = [{'s' : s, 'p' : p, 'o' : o, 'source' : source, 'support' : support} for (s,p,o, source, support) in triples]
		df = pd.DataFrame(data, columns=columns_order)
		df = df[columns_order]
		df.to_csv('out/all_triples.csv')


		print('# TRIPLES SELECTION')
		print(str(datetime.datetime.now()))
		s = Selector(triples)
		s.run()
		selected_triples = s.get_selected_triples()
		print('Number of triples:', len(triples))

		columns_order = ['s', 'p', 'o', 'source', 'support']
		data = [{'s' : s, 'p' : p, 'o' : o, 'source' : source, 'support' : support} for (s,p,o, source, support) in selected_triples]
		df = pd.DataFrame(data, columns=columns_order)
		df = df[columns_order]
		df.to_csv('out/selected_triples.csv')


		print('GRAPH BUILDING')
		print(str(datetime.datetime.now()))
		self.build_g(selected_triples)
		print('Saved Knowledge Graph with nodes:', len(self.g.nodes()), 'and edges:', len(self.g.edges()))
		nx.write_graphml(self.g, 'kg.graphml')

		


if __name__ == '__main__':
	builder = GraphBuilder('csv_e_r_full.csv')
	builder.pipeline()











