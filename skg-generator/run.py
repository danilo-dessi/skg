from classes.EntityCleaner import EntityCleaner
from classes.StatisticsRefiner import StatisticsRefiner
from classes.Mapper import Mapper
from classes.Selector import Selector
from classes.RelationsBuilder import RelationsBuilder
from classes.BestLabelFinder import BestLabelFinder

from gensim.models.keyedvectors import KeyedVectors

import sys
import pandas as pd
import ast
import networkx as nx
import Levenshtein.StringMatcher as ls
import datetime
import nltk
import numpy as np
from scipy import spatial
import operator
import random
import collections


class GraphBuilder:

	def __init__(self, inputFile):
		self.inputFile = inputFile
		self.inputDataFrame = None
		self.inputTexts = None
		self.entities = None
		self.relations = None
		self.g = nx.DiGraph()
		self.validEntities = set()


	def loadData(self):
		self.inputDataFrame = pd.read_csv(self.inputFile).head(5)


	def parse(self):
		self.entities = [ast.literal_eval(e) for e in self.inputDataFrame['entities_column'].tolist()]
		self.relations = [ast.literal_eval(r) for r in self.inputDataFrame['relations_column'].tolist()]
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
		for eList in self.entities:
			newEList = []
			for eSentence in eList:
				newESentence = []
				for e in eSentence:
					newESentence += [e.lower()]
				newEList += [newESentence]
			newInputEntities += [newEList]
		self.entities = newInputEntities

		newInputRelations = []
		for rList in self.relations:
			newRList = []
			for rSentence in rList:
				newRSentence = []
				for (s,p,o) in rSentence:
					newRSentence += [(s.lower(), p.lower(), o.lower())]
				newRList += [newRSentence]
			newInputRelations += [newRList]
		self.relations = newInputRelations


		
	def removeNoConnectedNodes(self):
		isolated_nodes = [n for n,d in self.g.degree() if d == 0]
		self.g.remove_nodes_from(isolated_nodes)


	def removeSelfEdges(self):
		self.g.remove_edges_from(self.g.selfloop_edges())


	def validate(self):
		allEntities = [] 
		for i in range(len(self.entities)):
			for eList in self.entities[i]:
				allEntities += [e for e in eList]

		allEntities = set(allEntities)	
		refiner = StatisticsRefiner(allEntities, self.entities, self.relations, 2, 10)
		self.validEntities, self.entities,  self.relations = refiner.validate()
		print('Entities after:', len(self.validEntities))


	def cleanEntities(self):
		entityCleaner = EntityCleaner(self.entities, self.relations, self.validEntities)
		entityCleaner.run()
		self.entities = entityCleaner.getEntitiesCleaned()
		self.relations = entityCleaner.getRelationsCleaned()
	 

	#BestLabelFinder module execution
	def build_triples(self):
		finder = BestLabelFinder(self.inputTexts, self.entities, self.relations)
		finder.run()
		return finder.get_triples()


	# Mapping of relations with our taxonomy using Mapper
	def get_mapped_triples(self, triples):
		m = Mapper(triples)
		m.run()
		return m.get_triples()

	def map_on_definitive_triples(self, triples):
		m = Mapper(triples)
		m.map_on_definitive_predicates()
		return m.get_triples()



	def save_pandas(self, triples, destination):
		columns_order = ['s', 'p', 'o', 'source', 'support']
		data = [{'s' : s, 'p' : p, 'o' : o, 'source' : source, 'support' : support} for (s,p,o, source, support) in triples]
		df = pd.DataFrame(data, columns=columns_order)
		df = df[columns_order]
		df.to_csv(destination)



	def build_g(self, selected_triples):

		id_gen = 0
		entity2id = {}
		id2entity = {}

		# a single id to each entity
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

		# graph generation
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

		print('# ENTITIES CLEANING')
		print(str(datetime.datetime.now()))
		self.cleanEntities()


		print('# TRIPLES GENERATION')
		print(str(datetime.datetime.now()))
		triples = self.build_triples()
		print('Number of triples:', len(triples))


		print('# TRIPLES MAPPING')
		print(str(datetime.datetime.now()))
		triples = self.get_mapped_triples(triples)
		print('Number of triples:', len(triples))
		self.save_pandas(triples, 'out/all_triples.csv')


		print('# TRIPLES SELECTION')
		print(str(datetime.datetime.now()))
		s = Selector(triples)
		s.run()
		selected_triples = s.get_selected_triples()
		discarded_triples = s.get_discarded_triples()
		print('Number of selected triples:', len(selected_triples))
		selected_triples = self.map_on_definitive_triples(selected_triples)
		discarded_triples = self.map_on_definitive_triples(discarded_triples)
		self.save_pandas(selected_triples, 'out/selected_triples.csv')
		self.save_pandas(discarded_triples, 'out/discarded_triples.csv')

		print('GRAPH BUILDING')
		print(str(datetime.datetime.now()))
		self.build_g(selected_triples)
		rb = RelationsBuilder(self.g)
		rb.run()
		self.g = rb.get_g()

		self.removeNoConnectedNodes()
		self.removeSelfEdges()
		nx.write_graphml(self.g, 'kg.graphml')
		print('Saved Knowledge Graph with nodes:', len(self.g.nodes()), 'and edges:', len(self.g.edges()))

		


if __name__ == '__main__':
	builder = GraphBuilder('csv_e_r_full_28_09_2019.csv')
	builder.pipeline()











