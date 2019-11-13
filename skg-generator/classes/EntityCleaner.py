import re
from nltk.corpus import stopwords
import string
from nltk.stem import WordNetLemmatizer
import nltk
from nltk.corpus import wordnet as wn
import spacy
from spacy.lang.en import LEMMA_INDEX, LEMMA_EXC, LEMMA_RULES

class EntityCleaner:
	def __init__(self, entities, relations, validEntities):
		self.entities = entities
		self.relations = relations
		self.validEntities = validEntities
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
		#print(entitiesMap)
		for r in relationsList:
			#print(r)
			
			A = r[0]
			relationLabel = r[1]
			B = r[2]

			newA = None
			newB = None
			if A in entitiesMap and B in entitiesMap: 
				newA = entitiesMap[A]
				newB = entitiesMap[B]
				relations += [(newA, relationLabel, newB)]
				#print((newA, relationLabel, newB))
			#print('-----------------------')
		#print(relations)
		#print('\n\n\n')
		return relations


	def puntuaction_and_stopword(self):
		
		stopWords = set(stopwords.words('english'))
		regex_puntuaction_ok = re.compile('[%s]' % re.escape("\"'-_`")) # possible characters
		puntuaction_reject = list("!#$%*+,./:;<=>?@%=[]^{|}~/{}`'") + ['\\']

		new_entities = []
		new_relations = []

		for paper_number in range(len(self.entities)):
			new_paper_entities = []
			new_paper_relations = []
			
			for sentence_number in range(len(self.entities[paper_number])):
				entities = self.entities[paper_number][sentence_number]
				relations = self.relations[paper_number][sentence_number]

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
				
						if tmpE not in stopWords and e in self.validEntities:
							new_sentence_entities += [tmpE]
							entitiesMap[e] = tmpE
							self.validEntities.add(tmpE)

				new_paper_entities += [new_sentence_entities]
				new_paper_relations += [self.updateRelations(relations, entitiesMap)]

			new_entities += [new_paper_entities]
			new_relations += [new_paper_relations]


		self.entities = new_entities
		self.relations = new_relations



	def lemmatize(self):
		
		entitiesMap = {}
		new_entities = []
		new_relations = []

		for paper_number in range(len(self.entities)):
			new_paper_entities = []
			new_paper_relations = []

			for sentence_number in range(len(self.entities[paper_number])):
				entities = self.entities[paper_number][sentence_number]
				relations = self.relations[paper_number][sentence_number]

				entitiesMap = {}
				new_sentence_entities = []
				new_sentence_relations = []

				for e in entities:

					if e in self.validEntities:
						tokens = self.spacy_tokenize(e)

						if len(tokens) > 1:
							lemma = sorted(self.lemmatizer(tokens[-1], u'NOUN'))[0]
							tmpE = ' '.join(tokens[:-1] + [lemma])
							new_sentence_entities += [tmpE]
							entitiesMap[e] = tmpE
							self.validEntities.add(tmpE)

						elif len(tokens) == 1:
							lemma = sorted(self.lemmatizer(tokens[0], u'NOUN'))[0]
							new_sentence_entities += [lemma]
							entitiesMap[e] = lemma
							self.validEntities.add(lemma)

				new_paper_entities += [new_sentence_entities]
				new_paper_relations += [self.updateRelations(relations, entitiesMap)]


			new_entities += [new_paper_entities]
			new_relations += [new_paper_relations]

		self.entities = new_entities
		self.relations = new_relations



	'''
	Methods entity_string_improvement() and improve_entities() remove characters that appear in some entities (e.g. 'ontology, # n #).
	They also remove entities that start with a number
	'''
	def entity_string_improvement(self, e):
		improved_entity_string = e.strip()
		first_character = improved_entity_string[0]
		last_character = improved_entity_string[-1]

		while(True):
			if first_character in list("!#$%*+,./:;<=>?@%=[]^{|}~/{}`' ") + ['\\']:
				improved_entity_string = improved_entity_string[1:]
				first_character = improved_entity_string[0]
				#print(e, '->', improved_entity_string)
			else:
				break

		while(True):
			if last_character in list("!#$%*+,./:;<=>?@%=[]^{|}~/{}`' ") + ['\\']:
				improved_entity_string = improved_entity_string[:-1]
				last_character = improved_entity_string[-1]
				#print(e, '->', improved_entity_string)
			else:
				break
		return improved_entity_string.strip()

	
	def improve_entities(self):
		
		new_entities = []
		new_relations = []

		for paper_number in range(len(self.entities)):
			new_paper_entities = []
			new_paper_relations = []

			for sentence_number in range(len(self.entities[paper_number])):
				entities = self.entities[paper_number][sentence_number]
				relations = self.relations[paper_number][sentence_number]

				new_sentence_entities = []
				new_sentence_relations = []
				entitiesMap = {}

				for e in entities:
					if not e[0].isdigit() and len(e) > 1: # first character must not be a number. The entity string must have at least two characters
						e_improved = self.entity_string_improvement(e)
						entitiesMap[e] = e_improved
						new_sentence_entities += [e_improved]

				new_paper_entities += [new_sentence_entities]
				new_paper_relations += [self.updateRelations(relations, entitiesMap)]

			new_entities += [new_paper_entities]
			new_relations += [new_paper_relations]

		self.entities = new_entities
		self.relations = new_relations


			
	def getEntitiesCleaned(self):
		return self.entities

	def getRelationsCleaned(self):
		return self.relations

	def run(self):
		self.improve_entities()
		self.puntuaction_and_stopword()
		self.lemmatize()



		all_entities = []
		all_relations = []
		for paper_number in range(len(self.entities)):
			new_paper_entities = []
			new_paper_relations = []

			for sentence_number in range(len(self.entities[paper_number])):
				entities = self.entities[paper_number][sentence_number]
				relations = self.relations[paper_number][sentence_number]

				all_entities += entities
				all_relations += relations
		for e in sorted(set(all_entities)):
			print(e)
		for r in sorted(set(all_relations)):
			print(r)

		exit(1)






		
	