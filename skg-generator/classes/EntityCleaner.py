import re
from nltk.corpus import stopwords
import string
from nltk.stem import WordNetLemmatizer
import nltk
from nltk.corpus import wordnet as wn
import spacy
from spacy.lang.en import LEMMA_INDEX, LEMMA_EXC, LEMMA_RULES

class EntityCleaner:
	def __init__(self, entities, relations, validEntities, rel2sent, id2sent):
		self.inputEntities = entities
		self.inputRelations = relations


		self.entitiesCleaned = []
		self.relationsCleaned = []

		self.validEntities = validEntities
		self.rel2sent = rel2sent
		self.id2sent = id2sent

		self.blackList = ['method', 'approach', 'tool', 'schema', 'model', 'framework', 'technology', 'term', \
		'document', 'algorithm', 'search', 'technique', 'system', 'paper', 'problem', 'software', 'application', 'it']

		self.nlp = spacy.load('en_core_web_sm')
		self.lemmatizer = spacy.lemmatizer.Lemmatizer(LEMMA_INDEX, LEMMA_EXC, LEMMA_RULES)


	def spacy_tokenize(self, text):
		doc = self.nlp(text)
		return [token.text for token in doc]

	'''
		- entitiesMap: a map of entities from old_entity_string to new_entity_string
		- relationsList: the list of relations containing the old entities strings that need to be updated to the new ones
	'''
	def updateRelations(self, relationsList, entitiesMap):
		
		relations = []
		for r in relationsList:
			
			A = r[0]
			relationLabel = r[1]
			B = r[2]

			newA = None
			newB = None
			if A in entitiesMap and entitiesMap[B]: 
				newA = entitiesMap[A]
				#if B in entitiesMap:
				newB = entitiesMap[B]

			if newA is not None and newB is not None:
				relations += [(newA, relationLabel, newB)]

				if r in self.rel2sent:
					self.rel2sent[(newA, relationLabel, newB)] = self.rel2sent[r]
					
		return relations


	def puntuaction_and_stopword(self):
		
		stopWords = set(stopwords.words('english'))
		regex_puntuaction_ok = re.compile('[%s]' % re.escape("\"'-_`")) # possible characters
		puntuaction_reject = list("!#$%*+,./:;<=>?@[\\]^{|}~")

		new_entities = []
		new_relations = []

		for paper_number in range(len(self.inputEntities)):
			new_paper_entities = []
			new_paper_relations = []
			
			for sentence_number in range(len(self.inputEntities[paper_number])):
				entities = self.inputEntities[paper_number][sentence_number]
				relations = self.inputRelations[paper_number][sentence_number]

				new_sentence_entities = []
				new_sentence_relations = []
				entitiesMap = {}

				for e in entities:
					valid_puntuaction = True
					for c in e:
						if c in puntuaction_reject:
							valid_puntuaction = False
							break

					if valid_puntuaction:
						tmpE = regex_puntuaction_ok.sub(' ', e)
						tmpE = tmpE.lower()
				
						if tmpE not in stopWords:
							new_sentence_entities += [tmpE]
							entitiesMap[e] = tmpE

						if e in self.validEntities:
							self.validEntities.add(tmpE)

				new_paper_entities += [new_sentence_entities]
				new_paper_relations += [self.updateRelations(relations, entitiesMap)]

			new_entities += [new_paper_entities]
			new_relations += [new_paper_relations]

		self.entitiesCleaned = new_entities
		self.relationsCleaned = new_relations



	def lemmatize(self):
		
		entitiesMap = {}
		new_entities = []
		new_relations = []

		for paper_number in range(len(self.inputEntities)):
			new_paper_entities = []
			new_paper_relations = []

			for sentence_number in range(len(self.inputEntities[paper_number])):
				entities = self.inputEntities[paper_number][sentence_number]
				relations = self.inputRelations[paper_number][sentence_number]

				entitiesMap = {}
				new_sentence_entities = []
				new_sentence_relations = []

				for e in entities:
					tokens = self.spacy_tokenize(e)
					if len(tokens) > 1:
						lemma = sorted(self.lemmatizer(tokens[-1], u'NOUN'))[0]
						tmpE = ' '.join(tokens[:-1] + [lemma])
						new_sentence_entities += [tmpE]
						entitiesMap[e] = tmpE

						if e in self.validEntities:
							self.validEntities.add(tmpE)
					elif len(tokens) == 1:
						lemma = sorted(self.lemmatizer(tokens[0], u'NOUN'))[0]
						new_sentence_entities += [lemma]
						entitiesMap[e] = lemma

						if e in self.validEntities:
							self.validEntities.add(lemma)

				new_paper_entities += [new_sentence_entities]
				new_paper_relations += [self.updateRelations(relations, entitiesMap)]

			new_entities += [new_paper_entities]
			new_relations += [new_paper_relations]

		self.entitiesCleaned = new_entities
		self.relationsCleaned = new_relations

			
	def getEntitiesCleaned(self):
		return self.entitiesCleaned

	def getRelationsCleaned(self):
		return self.relationsCleaned

	def run(self):
		self.puntuaction_and_stopword()
		self.lemmatize()






		
	