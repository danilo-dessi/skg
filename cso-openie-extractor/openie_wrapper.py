from stanfordcorenlp import StanfordCoreNLP
import datetime
import json
import nltk
import pandas as pd


class OPENIE_wrapper:
	def __init__(self):
	   
		self.relations = []
		self.stanford_path = r'../stanford-corenlp-full-2018-10-05'  
		self.nlp = StanfordCoreNLP(self.stanford_path, memory='8g')
		print(str(datetime.datetime.now()) + ' Openie connection up')


	def restart_corenlp(self):
		self.nlp.close()
		self.nlp = StanfordCoreNLP(self.stanford_path, memory='8g')

	def close(self):
		self.nlp.close()

	def __build_pos_map(self, tokens):
		word2pos = {}
		for token in tokens:
			word2pos[token['word']] = token['pos']
		return word2pos

	def __token_index2lemma(self, tokens):
		token_index2lemma = {}
		for token in tokens:
			token_index2lemma[token['index']] = token['lemma']
		return token_index2lemma



	def run(self, text, entities):
		self.relations = []
		self.corenlp_data = {}

		print(text)
		props = {'annotators': 'openie,coref', 'pipelineLanguage': 'en', 'outputFormat': 'json'}
		try:
			corenlp_out = json.loads(self.nlp.annotate(text, properties=props))
		except:
			self.nlp.close()
			print('Stanford Core NLP is not responding. Please try later')
			exit(1)
		
		corefs_map = {}
		for coref_number in corenlp_out['corefs']:
			representative_coref = corenlp_out['corefs'][coref_number][0]
			for i in range(1, len(corenlp_out['corefs'][coref_number])):
				coref = corenlp_out['corefs'][coref_number][i]
				corefs_map[coref['text']] = representative_coref['text']


		for sentence in corenlp_out['sentences']:

			word2pos = self.__build_pos_map(sentence['tokens'])
			token_index2lemma = self.__token_index2lemma(sentence['tokens'])
			for openie_relation in sentence['openie']:
				
				only_verbs = True
				for word in nltk.word_tokenize(openie_relation['relation']):
					if word not in word2pos or word2pos[word] not in ['MD', 'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ']:
						only_verbs = False
						break

				if only_verbs:
					relation_span = openie_relation['relationSpan']
					relation = ''
					for v in range(relation_span[1] - relation_span[0]):
						relation += ' ' + token_index2lemma[relation_span[0] + v + 1]
					relation = 'v-' + relation[1:]

					if openie_relation['subject'] in entities:
						ok = True
						for word in nltk.word_tokenize(openie_relation['object']):
							if word not in word2pos or word2pos[word] not in ['MD', 'NN', 'NNP', 'NNPS', 'NNS', 'JJ']:
								ok = False
								break
						if ok:
							subject = openie_relation['subject'] if openie_relation['subject'] not in corefs_map else corefs_map[openie_relation['subject']]
							object = openie_relation['object'] if openie_relation['object'] not in corefs_map else corefs_map[openie_relation['object']]
							self.relations += [(subject, relation, object)]
							print('Final:', (subject, relation, object))
					
					elif openie_relation['object'] in entities:
						ok = True
						for word in nltk.word_tokenize(openie_relation['subject']):
							if word not in word2pos or word2pos[word] not in ['NN', 'NNP', 'NNPS', 'NNS', 'JJ']:
								ok = False
								break
						if ok:
							subject = openie_relation['subject'] if openie_relation['subject'] not in corefs_map else corefs_map[openie_relation['subject']]
							object = openie_relation['object'] if openie_relation['object'] not in corefs_map else corefs_map[openie_relation['object']]
							self.relations += [(subject, relation, object)]
							print('Final:', (subject, relation, object))	

		self.nlp.close()
		return self.relations


if __name__ == '__main__':
	corenlp = OPENIE_wrapper()
	text1 = 'Clients ( human and agent ) can query Linked Data from multiple sources at once and combine it on the fly'
	entities1 = ['it', 'Linked Data', 'Clients']
	
	text2 = 'There are a number of online tools that try to identify named entities in text and link them to linked data resources '
	entities2 = ['them', 'online tools', 'named entities', 'linked data resources']
	
	text3 = 'The semantic web is a web of data that make capable machines to understand the data on web pages and also known as Web 3.0 .'
	entities3 = ['web pages', 'web of data', 'Web 3.0', 'semantic web']

	text4 = 'There has recently been an upsurge of interest in the possibilities of combining structured data and ad-hoc information retrieval from traditional hypertext'
	entities4 = ['structured data', 'hypertext', 'ad-hoc information retrieval']

	#definition
	text5 = 'The Semantic Web is an extension of the World Wide Web in which data is structured and XML-tagged on the basis of its meaning or content, so that computers can process and integrate the information without human intervention:'
	
	#definition
	text6 = 'The Smart Topic Miner (STM) is a novel application, developed in collaboration with Springer Nature, which classifies scholarly publications according to an automatically generated ontology of research areas. '
	
	text7 = 'Results show that Semantic Web systems are a good option for complicated problems needing high expressiveness .'
	entities7 = ['Semantic Web systems']

	text8 = 'According to the characteristics and requirement of the semantic Web , a kind of new description logic , i.e. , fuzzy dynamic description logic FDDL , is presented '
	entities8 = ['fuzzy dynamic description logic FDDL', 'description logic', 'semantic Web']

	corenlp.run(text7, entities7)





