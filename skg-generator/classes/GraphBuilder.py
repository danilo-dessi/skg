from EntityCleaner import EntityCleaner
from RelationsManager import RelationsManager
from EntityClustering import EntityClustering
from RelationsDeepFinder import RelationsDeepFinder
from RelationsBuilder import RelationsBuilder
from StatisticsRefiner import StatisticsRefiner
from Clusterizer import Clusterizer
from Mapper import Mapper
from Selector import Selector

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

	def integrateInputData(self):
		data = pd.read_csv(self.inputFile)
		data['entities_in_graph'] = self.entitiesInGraph
		data['relations_in_graph'] = self.relationsInGraph
		data.to_csv(self.outputFile.replace('.graphml', '_integrated.csv'))


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

	def getEntity2embedding(self):
		
		model = KeyedVectors.load_word2vec_format('../resources/9M[300-5]_skip_gram.bin', binary=True)

		for paper_number in range(len(self.inputTexts)):
			for sentence_number in range(len(self.inputTexts[paper_number])):
				entities = self.entitiesCleaned[paper_number][sentence_number]
				for e in entities:
					if e not in self.entity2embedding:
						if e.replace(' ', '_') in model:
							self.entity2embedding[e] = model[e.replace(' ', '_')]
						else:
							emb = np.array([])
							tokens = nltk.word_tokenize(e)

							foundTokens = 0
							for token in tokens:
								if token in model:
									emb = np.concatenate((emb, model[token]), axis=None)
									foundTokens += 1
							if foundTokens == len(tokens):
								self.entity2embedding[e] = emb
							else: 
								self.entity2embedding[e] = np.array([]) 


	def mapWithClustering(self):

		setsLabels = {} #set of labels with emebeddings of the same size in order to compute the clustering
		setsEmbeddings = {}

		for e in self.entity2embedding:
			if len(self.entity2embedding[e]) not in setsLabels and len(self.entity2embedding[e]) > 0:
				setsLabels[len(self.entity2embedding[e])] = []
				setsEmbeddings[len(self.entity2embedding[e])] = []

			if len(self.entity2embedding[e]) > 0:
				setsLabels[len(self.entity2embedding[e])] += [e]
				setsEmbeddings[len(self.entity2embedding[e])] += [self.entity2embedding[e]]

		for k in setsEmbeddings:
			newMaps = Clusterizer.run(setsLabels[k], setsEmbeddings[k])
			self.entitiesEmbeddingsMap.update(newMaps)
			


	def assemblyEntities(self):

		globalSimilarEntities = {}
		entitiesLabelsMap = {}

		self.getEntity2embedding()
		self.mapWithClustering()

		idGenerator = 1
		newEntitiesCleaned = []
		newRelationsCleaned = []
		
		for paper_number in range(len(self.entitiesCleaned)):
			new_paper_entities = []
			new_paper_relations = []

			for sentence_number in range(len(self.entitiesCleaned[paper_number])):

				new_sentence_entities = []
				new_sentence_relations = []
				entities = self.entitiesCleaned[paper_number][sentence_number]
				relations = self.relationsCleaned[paper_number][sentence_number]

				for e in entities:
					label = e
					if e in self.entitiesEmbeddingsMap:
						label = self.entitiesEmbeddingsMap[e]
					new_sentence_entities += [label]

				for r in relations:
					A = r[0]
					relationLabel = r[1]
					B = r[2]

					Adep = r[3]
					Bdep = r[4]
					sc = r[5]

					rel = None
					if A in self.entitiesEmbeddingsMap and B in self.entitiesEmbeddingsMap and A in entities and B in entities:
						rel = (self.entitiesEmbeddingsMap[A], relationLabel, self.entitiesEmbeddingsMap[B], Adep, Bdep, sc)
						new_sentence_relations += [rel]
						
					elif A in self.entitiesEmbeddingsMap and B not in self.entitiesEmbeddingsMap and A in entities and B in entities:
						rel = (self.entitiesEmbeddingsMap[A], relationLabel, B, Adep, Bdep, sc)
						new_sentence_relations += [rel]

					elif A not in self.entitiesEmbeddingsMap and B in self.entitiesEmbeddingsMap and A in entities and B in entities:
						rel = (A, relationLabel, self.entitiesEmbeddingsMap[B], Adep, Bdep, sc)
						new_sentence_relations += [rel]

					elif A in entities and B in entities:
						rel = (A, relationLabel, B, Adep, Bdep, sc)
						new_sentence_relations += [rel]

				new_paper_entities += [new_sentence_entities]
				new_paper_relations += [new_sentence_relations]

			newEntitiesCleaned += [new_paper_entities]
			newRelationsCleaned += [new_paper_relations]

		self.entitiesCleaned = newEntitiesCleaned
		self.relationsCleaned = newRelationsCleaned

		#free memory
		self.entitiesEmbeddingsMap = {}
		self.entity2embedding = {}

		


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
		#this is the new viariant of makeRelations. This doenn't save on files but directly returns the triples
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



	def makeRelations(self):
		model = KeyedVectors.load_word2vec_format('../resources/9M[300-5]_skip_gram.bin', binary=True)
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
			triples += [(s, best_label, o, 'openie', support)]


		#saving verbs window relations
		data =[]
		for (s,o) in so2verbs:

			verbs = so2verbs[(s,o)]
			labels = self.flatWordsOnAverage(verbs, model)			
			best_label = labels[0]
			support = len(verbs)
			
			# BEST LABEL
			sentences_best_label = spo2sentences[(s,best_label,o)]
			for v in verbs:
				if (v not in labels):
					sentences_best_label += spo2sentences[(s,v,o)]

			otherInfo = None
			for i in range(len(so2other[(s,o)])):
				if so2verbs[(s,o)][i] == best_label:
					otherInfo =  so2other[(s,o)][i]
					break	
			data += [{'s':s , 'p': best_label, 'o': o, 'support': support, 'best_predicate':'yes', 'all_predicates':verbs, 'sDep': otherInfo[0], 'oDep': otherInfo[1], 'sc': otherInfo[2], 'all_sentences':list(set(sentences_best_label)), 'source':'heuristic'}]

			# LABEL THAT ARE NOT SIMILAR TO AVERAGED VERBS
			sentences = []
			for v in set(labels[1:]):
				sentences = spo2sentences[(s,v,o)]
				for i in range(len(so2other[(s,o)])):
					if so2verbs[(s,o)][i] == v:
						otherInfo =  so2other[(s,o)][i]
						break
				data += [{'s':s , 'p': v, 'o': o, 'support': support, 'best_predicate':'no', 'sDep': otherInfo[0], 'oDep': otherInfo[1], 'sc': otherInfo[2], 'all_predicates':verbs, 'all_sentences':list(set(sentences)), 'source':'heuristic'}]


		column_order = ['s', 'p', 'o', 'support', 'best_predicate', 'sDep', 'oDep', 'sc', 'all_predicates', 'all_sentences', 'source']
		df = pd.DataFrame(data, columns=column_order)
		df = df[column_order]
		df.to_csv('../out/relations.csv')


		#saving openie relations
		data = []
		for (s,o) in so2openie_verbs:
			verbs = so2openie_verbs[(s,o)]
			labels = self.flatWordsOnAverage(verbs, model)			
			best_label = labels[0]
			support = len(verbs)

			sentences = spo_openie2sentences[(s, best_label, o)]
			for v in verbs:
				if (v not in labels):
					sentences += spo_openie2sentences[(s,v,o)]
			data += [{'s':s , 'p': best_label, 'o': o, 'support': support, 'best_predicate':'yes', 'all_predicates':verbs, 'all_sentences': list(set(sentences)), 'source':'openie'}]

			for label in set(labels[1:]):
				sentences = spo_openie2sentences[(s, label, o)]
				data += [{'s':s , 'p': label, 'o': o, 'support': support, 'best_predicate':'no', 'all_predicates':verbs, 'all_sentences':list(set(sentences)), 'source':'openie'}]

		
		column_order = ['s', 'p', 'o', 'support', 'best_predicate', 'all_predicates', 'all_sentences', 'source']
		df = pd.DataFrame(data, columns=column_order)
		df = df[column_order]
		df.to_csv('../out/openIErelations.csv')


		#saving luanyi relations
		data = []
		for (s,o) in so2luanyi:

			labels = so2luanyi[(s,o)]
			support = len(labels)
			counter = collections.Counter(labels)
			frequencies = sorted(counter.items(), key=operator.itemgetter(1), reverse=True)
			most_frequent_label = frequencies[0][0]
			other_labels = set([l for (l,c) in frequencies[1:]])
			#print(s, o , labels)
			#print(counter)
			#print(frequencies)
			#print(most_frequent_label)


			sentences = spo_luanyi2sentences[(s, most_frequent_label, o)]
			for label in other_labels:
					sentences += spo_luanyi2sentences[(s, label,o)]
			data += [{'s':s , 'p': most_frequent_label, 'o': o, 'support': support, 'best_predicate':'yes', 'all_labels':labels, 'all_sentences': list(set(sentences)), 'source':'luanyi'}]
		
		column_order = ['s', 'p', 'o', 'support', 'best_predicate', 'all_predicates', 'all_sentences', 'source']
		df = pd.DataFrame(data, columns=column_order)
		df = df[column_order]
		df.to_csv('../out/luanyi_relations.csv')




		exit(1)


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
		allEntities = [] #set([e.lower() for eList self.inputEntities for e in eList])
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

		print('# GRAPH BUILDING')
		print(str(datetime.datetime.now()))
		#self.assemblyEntities()

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


		exit(1)

		self.build2()
		exit(1)

		print(str(datetime.datetime.now()), '# No connected nodes remotion')
		self.removeNoConnectedNodes()

		print(str(datetime.datetime.now()), '# Self edges remotion')
		self.removeSelfEdges()

		print(str(datetime.datetime.now()), '# CSO relations integration')
		self.addRelations()

		
		self.save()
		print('DONE')

		#self.integrateInputData()
		


if __name__ == '__main__':
	builder = GraphBuilder(sys.argv[1], sys.argv[2])
	#print(builder.simWithEmbeddings('semantic learning', 'semantic learning'))
	builder.pipeline()
	#g = nx.read_graphml('../out/semantic_web.graphml')
	#c = EntityClustering(g)
	#c.run()











