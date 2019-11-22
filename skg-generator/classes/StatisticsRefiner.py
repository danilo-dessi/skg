import datetime
import csv
from urllib.parse import unquote
import pandas as pd
import re
import string
import regex
import nltk

class StatisticsRefiner:
	def __init__(self, entities, inputEntities, inputRelations, thCS, thGD):
		self.thCS = thCS
		self.thGD = thGD
		self.entities = entities

		self.inputEntities = inputEntities
		self.inputRelations = inputRelations

		self.csoResourcePath = 'resources/CSO.3.1.csv'
		self.keywordsPath  = 'resources/semantic_web_keywords.txt'
		self.semanticWebAbstractsPath = 'resources/semantic_web_28k_abstracts.txt'
		self.computerScienceAbstractsPath = 'resources/computer_science_28k_abstracts.txt'
		self.generalDomainAbstractsPath = 'resources/general_domain_28k_abstracts.txt'
		
		self.csoTopics = set()
		self.semanticWebKeywords = set()
		self.semanticWebAbstracts = []
		self.computerScienceAbstracts = []
		self.generalDomainAbstracts = []

		self.statistics = {}
		self.validEntities = set()
		self.blackList = set(['method', 'approach', 'tool', 'schema', 'model', 'framework', 'technology', 'term', \
		'document', 'algorithm', 'search', 'technique', 'system', 'paper', 'problem', 'software', 'component', 'it', \
		'activity', 'agent', 'application', 'architecture', 'context', 'keyword', 'set', 'workflow', 'prototype'])



	def keepOnlyValid(self):
		newEntities = []
		newRelations = []
		for paper_number in range(len(self.inputEntities)):
			
			newEntities_paper = []
			newRelations_paper = []

			for sentence_number in range(len(self.inputEntities[paper_number] )):
				newEntities_sentence = []
				newRelations_sentence = []

				for e in self.inputEntities[paper_number][sentence_number]:
					if e.lower() in self.validEntities:
						newEntities_sentence += [e.lower()]
			
				newEntities_paper += [newEntities_sentence]

				for r in self.inputRelations[paper_number][sentence_number]:
					if r[0].lower() in self.validEntities and r[2].lower() in self.validEntities:
						newRelations_sentence += [(r[0].lower(),r[1],r[2].lower())]
				newRelations_paper += [newRelations_sentence]

			newEntities += [newEntities_paper]
			newRelations += [newRelations_paper]
			
		return newEntities, newRelations



	def loadCSOTopics(self):
		with open(self.csoResourcePath, 'r', encoding='utf-8') as csv_file:
			csv_reader = csv.reader(csv_file, delimiter=',')
			for row in csv_reader:
				t1 = unquote(row[0]).replace('<https://', '')[:-1]
				t2 = unquote(row[2]).replace('<https://', '')[:-1]
				if t1.startswith('cso.kmi.open.ac.uk/topics/'):
					t1 = t1.split('/')[-1]
					self.csoTopics.add(t1.lower())
				if t2.startswith('cso.kmi.open.ac.uk/topics/'):
					t2 = t2.split('/')[-1]
					self.csoTopics.add(t2.lower())

	def loadKeywords(self):
		with open(self.keywordsPath, 'r', encoding='utf-8') as f:
			for row in f.readlines():
				self.semanticWebKeywords.add(row.strip().lower())

	def loadAbstracts(self):
		
		with open(self.semanticWebAbstractsPath, 'r', encoding='utf-8') as f:
			self.semanticWebAbstracts = f.read().lower()

		with open(self.computerScienceAbstractsPath, 'r', encoding='utf-8') as f:
			self.computerScienceAbstracts = f.read().lower()

		with open(self.generalDomainAbstractsPath, 'r', encoding='utf-8') as f:
			self.generalDomainAbstracts = f.read().lower()


	def computeOccurrenciesOnAbstractsNew(self):
		semanticWebCount = []
		generalDomainCount = []
		computerScienceCount = []
		alreadySeenEntities = set()
		data = []

		tokens = nltk.word_tokenize(self.semanticWebAbstracts)
		tot_target_domain = len(tokens)

		tokens = nltk.word_tokenize(self.computerScienceAbstracts)
		tot_computer_science_domain = len(tokens)

		tokens = nltk.word_tokenize(self.generalDomainAbstracts)
		tot_general_domain = len(tokens)

		for e in self.entities:
			if e not in alreadySeenEntities and e not in self.validEntities:
				alreadySeenEntities.add(e)
				c = str(self.semanticWebAbstracts).count( str(e.strip().lower()) )
				semanticWebCount += [c / tot_target_domain]

				c = str(self.computerScienceAbstracts).count(str(e.strip().lower()) )
				computerScienceCount += [c / tot_computer_science_domain]

				c = str(self.generalDomainAbstracts).count( str(e.strip().lower()) )
				generalDomainCount += [c / tot_target_domain]

				self.statistics[e] = {}

				'''if(computerScienceCount[-1] > 0) and generalDomainCount[-1] > 0:
					print('\nEntity:', e)
					print('SW c:', semanticWebCount[-1], semanticWebCount[-1]/tot_target_domain)
					print('CS c:', computerScienceCount[-1], computerScienceCount[-1]/tot_computer_science_domain)
					print('GE c:', generalDomainCount[-1], generalDomainCount[-1]/tot_computer_science_domain)
					print('SW-CS c:', (semanticWebCount[-1]/tot_target_domain) / (computerScienceCount[-1]/tot_computer_science_domain))
					print('SW-GE c:', (semanticWebCount[-1]/tot_target_domain) / (generalDomainCount[-1]/tot_computer_science_domain))
				else:
					print('\nEntity:', e)
					print('SW c:', semanticWebCount[-1], semanticWebCount[-1]/tot_target_domain)
					print('CS c:', computerScienceCount[-1], computerScienceCount[-1]/tot_computer_science_domain)
					print('GE c:', generalDomainCount[-1], generalDomainCount[-1]/tot_computer_science_domain)'''
				

				if computerScienceCount[-1] > 0:
					self.statistics[e]['sw&cs'] = semanticWebCount[-1] / computerScienceCount[-1]
				else: 
					self.statistics[e]['sw&cs'] = 10

				if generalDomainCount[-1] > 0:
					self.statistics[e]['sw&gd'] = semanticWebCount[-1] / generalDomainCount[-1]
				else:
					self.statistics[e]['sw&gd'] = 20
	
				data += [{ 'entity' : e, 'sw-count': semanticWebCount[-1], 'cs-count': computerScienceCount[-1], 'gd-count':generalDomainCount[-1], 'sw&cs': self.statistics[e]['sw&cs'], 'sw&gd': self.statistics[e]['sw&gd'] }]

		column_order = ['entity', 'sw-count', 'cs-count', 'gd-count', 'sw&cs', 'sw&gd' ]
		df = pd.DataFrame(data, columns=column_order)
		df = df[column_order]
		df.to_csv('out/entities-statistics.csv')

	def statsValidation(self):
		validEntities = []
		for e in self.entities:
			if e not in self.validEntities:
				if self.statistics[e]['sw&cs'] >= self.thCS and self.statistics[e]['sw&gd'] >= self.thGD:
					validEntities += [e]
				
		return set(validEntities)


	def csoValidation(self):
		validEntities = []
		for e in self.entities:
			if e not in self.validEntities:
				if e.lower() in self.csoTopics:
					validEntities += [e]
		return set(validEntities)


	def keywordsValidation(self):
		validEntities = []
		for e in self.entities:
			if e not in self.validEntities:
				if e.lower() in self.semanticWebKeywords:
					validEntities += [e]
		return set(validEntities)


	def validate(self):

		print('Entities to validate:', len(self.entities))

		self.loadCSOTopics()
		validatedCSO = self.csoValidation()
		self.validEntities = self.validEntities | validatedCSO
		print('Entities validated with CSO:', len(validatedCSO))


		self.loadKeywords()
		validatedKeywords = self.keywordsValidation()
		self.validEntities = self.validEntities | validatedKeywords
		print('Entities validated with Keywords:', len(validatedKeywords))


		self.loadAbstracts()
		self.computeOccurrenciesOnAbstractsNew()
		validatedStatistics = self.statsValidation()
		self.validEntities = self.validEntities | validatedStatistics
		print('Entities validated with Statistics:', len(validatedStatistics))

		self.validEntities = set([e.lower() for e in self.validEntities])
		self.validEntities = self.validEntities.difference(self.blackList)
		finalEntities, finalRelations = self.keepOnlyValid()

		return self.validEntities, finalEntities, finalRelations

		







