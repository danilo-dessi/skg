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

	def __init__(self, inputFile, outputFile):
		self.inputFile = inputFile
		self.outputFile = outputFile
		self.inputDataFrame = None
		self.inputEntities = None
		self.inputRelations = None
		self.inputTexts = None
		
		self.relationsRefined = None
		self.entitiesCleaned = None
		self.relationsCleaned = None
		self.verbsMap = None
		self.entitiesEmbeddingsMap = {}
		self.entity2embedding = {}
		self.g = nx.DiGraph()
		self.node2label = {}
		self.label2node = {}
		self.edge2label = {}
		self.edge2weight = {}
		self.validEntities = set()
		self.rel2sent = {}
		self.so2bestRelation = {}
		self.id2sent = None
		self.entitiesInGraph = []
		self.relationsInGraph = []


	def loadData(self):
		self.inputDataFrame = pd.read_csv(self.inputFile).head(50)


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

		

	def manageRelations(self):
		relationsManager = RelationsManager()
		relationsManager.run()
		self.verbsMap = relationsManager.getVerbsMap()

	def manageRelations_old(self):
		relationsManager = RelationsManager(self.relationsCleaned)
		relationsManager.run_old()
		self.verbsMap = relationsManager.getVerbsMap()


	def simWithEmbeddings(self, e1, e2):
		e1Tokens = nltk.word_tokenize(e1)
		e2Tokens = nltk.word_tokenize(e2)

		if e1 == e2:
			return 1.0
		e1emb = self.entity2embedding[e1]
		e2emb = self.entity2embedding[e2]

		if e1emb.shape == e2emb.shape and e1emb.size != 0:
			return 1 - spatial.distance.cosine(e1emb, e2emb)
		
		return 0.0

			

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
		model = KeyedVectors.load_word2vec_format('../resources/9M[100-5].bin', binary=True)
		so2verbs = {}
		so2other = {}
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

				for (s,p,o, sDep, oDep, sc) in relations:
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
							so2other[(s,o)] = []

						if (s,p,o) not in spo2sentences:
							spo2sentences[(s,p,o)] = []

						so2verbs[(s,o)] += [p]
						so2other[(s,o)] += [(sDep, oDep, sc)] 
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
			other_labels = set([l for (l,c) in frequencies[1:]])
			triples += [(s, best_label, o, 'luanyi', support)]

		return triples



	def build2(self):
		idGenerator = 1

		for paper_number in range(len(self.entitiesCleaned)):
			for sentence_number in range(len(self.entitiesCleaned[paper_number])):

				entities = self.entitiesCleaned[paper_number][sentence_number]
				relations = self.relationsCleaned[paper_number][sentence_number]

				for e in entities:
					self.g.add_node(idGenerator, label=e)
					self.node2label[idGenerator] = e
					self.label2node[e] = idGenerator
					idGenerator += 1

		#DANILO: DA QUI solo dopo aver definito l'approccio della valutazione delle triple



		rel2bestLabel, rel2weight, rel2source = self.makeRelations()
		for r in rel2bestLabel:
			idA = self.label2node[r[0]]
			idB = self.label2node[r[1]]
			self.g.add_edge(idB, idA, label=' - '.join(rel2bestLabel[r]), weight=rel2weight[r], source=rel2source[r])

		
	def removeNoConnectedNodes(self):
		isolated_nodes = [n for n,d in self.g.degree() if d == 0]
		self.g.remove_nodes_from(isolated_nodes)

	def removeSelfEdges(self):
		self.g.remove_edges_from(self.g.selfloop_edges())

	def save(self):
		print('Nodes:', len(self.g.nodes()), 'Edges:', len(self.g.edges()))
		nx.write_graphml(self.g, self.outputFile)

	def addRelations(self):
		r = RelationsBuilder(self.g)
		r.run()


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
		#print('Relations before refinement:', sum([len(relation) for relation in self.inputRelations]))
		self.relationsRefined = refiner.run() #, self.rel2sent, self.id2sent
		#print('Relations after refinement:', sum([len(relation) for relation in self.relationsRefined]))


	def cleanEntities(self):
		entityCleaner = EntityCleaner(self.inputEntities, self.relationsRefined, self.validEntities, self.rel2sent, self.id2sent)
		entityCleaner.run()

		self.relationsRefined = None
		self.entitiesCleaned = entityCleaner.getEntitiesCleaned()
		self.relationsCleaned = entityCleaner.getRelationsCleaned()


		
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
		m = Mapper(triples)
		m.run()
		triples = m.get_triples()
		print('Number of triples:', len(triples))

		columns_order = ['s', 'p', 'o', 'source', 'support']
		data = [{'s' : s, 'p' : p, 'o' : o, 'source' : source, 'support' : support} for (s,p,o, source, support) in triples]
		df = pd.DataFrame(data, columns=columns_order)
		df = df[columns_order]
		df.to_csv('../out/all_triples.csv')


		print('# TRIPLES SELECTION')
		s = Selector(triples)
		s.run()
		selected_triples = s.get_selected_triples()
		print('Number of triples:', len(triples))

		columns_order = ['s', 'p', 'o', 'source', 'support']
		data = [{'s' : s, 'p' : p, 'o' : o, 'source' : source, 'support' : support} for (s,p,o, source, support) in selected_triples]
		df = pd.DataFrame(data, columns=columns_order)
		df = df[columns_order]
		df.to_csv('../out/selected_triples.csv')

		


if __name__ == '__main__':
	builder = GraphBuilder(sys.argv[1], sys.argv[2])
	builder.pipeline()











