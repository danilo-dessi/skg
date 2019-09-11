#from cso_wrapper import CSO_wrapper
from openie_wrapper import OPENIE_wrapper
import pandas as pd
import sklearn as sk
import time
import ast 
import string 
import json
import numpy as np
import operator
from sklearn.feature_extraction.text import TfidfVectorizer
from stanfordcorenlp import StanfordCoreNLP
import traceback
import requests
import rdflib
from nltk import word_tokenize
from nltk.stem.lancaster import LancasterStemmer
import nltk
from nltk.tokenize import sent_tokenize
from nltk import tokenize
from threading import Thread
import urllib
import itertools
import datetime
import os
import datetime
import classifier.classifier as CSO

class Analyzer:

	def __init__(self):
		self.entities = {}
		self.relations = {}
		#self.cso = CSO_wrapper()
		self.openie = OPENIE_wrapper()

	def restart(self):
		self.openie.restart_corenlp()


	def close(self):
		self.openie.close()

	def find_str(self, s, char):
		index = 0
		if char in s:
			c = char[0]
			for ch in s:
				if ch == c:
					if s[index : index + len(char)] == char:
						return index
				index += 1
		return -1

	def intersection(self, start_1, end_1, start_2, end_2):
		return not(end_1 < start_2 or end_2 < start_1)

	def prepare_entities(self, sentence, luanyi_entities):
		entities = {}

		#entity luanyi preparation
		for e in luanyi_entities:
			start_index = self.find_str(sentence, e)
			if start_index != -1:
				entities[e] = {'start' : start_index, 'end' : start_index + len(e)}

		#cso entity preparatiom
		#try:
		#	cso_entities = self.cso.apply(sentence.lower())
		#	entities.update(cso_entities)
		#except:
		#	print('cso error on sentence:', sentence.lower())
		
		keys = list(entities.keys())
		entities_copy = dict(entities)
		for i in range(len(keys) - 1):
			key_i = keys[i]
			candidate = key_i
			for j in range(i + 1, len(keys)):
				key_j = keys[j]

				start_key_i = entities[key_i]['start']
				end_key_i = entities[key_i]['end']
				start_key_j = entities[key_j]['start']
				end_key_j = entities[key_j]['end']

				if self.intersection(start_key_i, end_key_i, start_key_j, end_key_j):
					if len(key_j) > len(key_i):
						entities_copy.pop(key_i, None)
					else:
						entities_copy.pop(key_j, None)

		entities = entities_copy
		return entities

	def analyze(self, text, entities):
		self.entities = self.prepare_entities(text, entities)
		self.relations = self.openie.run(text, self.entities)
		return self.relations


if __name__ == '__main__':
	
	analyzer = Analyzer()

	file_out = 'csv_e_r_full.csv'
	r_data = []

	file = 'luanyi_output.csv'
	print('start processing', file,  str(datetime.datetime.now()))
	data = pd.read_csv(file)
	print(data.describe())

	sentences_list = [ast.literal_eval(x) for x in data['sentences'].tolist()]
	sentences_entities_list = [ast.literal_eval(x) for x in data['entities'].tolist()]
	sentences_relations_list = [ast.literal_eval(x) for x in data['relations'].tolist()]


	#Extraction with CSO in batch mode
	papers = {}
	for n_abstract in range(len(sentences_list)):
		sentences = sentences_list[n_abstract]
		for n_sentence in range(len(sentences)):
			sentence = sentences_list[n_abstract][n_sentence]
			paper = {
				"title": "",
				"abstract": sentence,
				"keywords": ""
			}
			papers[str(n_abstract) + '.' + str(n_sentence)] = paper

	cso_result = CSO.run_cso_classifier_batch_mode(papers, workers = 2, modules = "both", enhancement = "first")


	for n_abstract in range(len(sentences_list)):
		print('\n# Analyzing abstract', n_abstract, '/', len(sentences_list))
		sentences = sentences_list[n_abstract]
		entities_list = sentences_entities_list[n_abstract]
		relations_list = sentences_relations_list[n_abstract]
		new_entities_list = []
		new_relations_list = []

		for n_sentence in range(len(sentences)):
			sentence = sentences[n_sentence]
			luanyi_entities = [e for (e, t) in entities_list[n_sentence]]
			luanyi_relations = relations_list[n_sentence]

			cso_entities = cso_result[str(n_abstract) + '.' + str(n_sentence)]['semantic']
			print(sentences_list[n_abstract][n_sentence], '\n', cso_entities)
			openie_relations = analyzer.analyze(sentence, luanyi_entities + cso_entities)
			new_entities_list += [list(set(luanyi_entities + cso_entities))]
			new_relations_list += [luanyi_relations + openie_relations]
			
		r_data += [{'sentences':sentences, 'entities_column':new_entities_list, 'relations_column':new_relations_list}]

		if len(r_data) % 1000 == 0:
			analyzer.restart()
			df = pd.DataFrame(r_data)
			df.to_csv(file_out)

	df = pd.DataFrame(r_data)
	df.to_csv(file_out)











