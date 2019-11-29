from stanfordcorenlp import StanfordCoreNLP
import datetime
import json
import nltk
import pandas as pd


class OPENIE_wrapper:
	def __init__(self, nlp):  
		self.relations = []
		self.stanford_path = r'../stanford-corenlp-full-2018-10-05'  
		self.nlp = nlp 

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

	def restart_nlp(self):
		self.nlp.close()
		self.nlp = StanfordCoreNLP(self.stanford_path, memory='6g')
		self.openie = OPENIE_wrapper(self.nlp)
		self.verb_finder = VerbWindowFinder(self.nlp)



	def run(self, text, entities):
		self.relations = []
		self.corenlp_data = {}

		try_restart_exception_raised = 3
		while(try_restart_exception_raised > 0):

			props = {'annotators': 'openie,coref', 'pipelineLanguage': 'en', 'outputFormat': 'json'}
			try:
				corenlp_out = json.loads(self.nlp.annotate(text, properties=props))
				try_restart_exception_raised = -1
			except:
				try_restart_exception_raised -= 1
				self.restart_nlp()


		if try_restart_exception_raised == 0:
			print('Error on the text:', text)
			return []
			
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
					relation = 'openie-' + relation[1:]

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
							#print('Final:', (subject, relation, object))
					
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
							#print('Final:', (subject, relation, object))	

			return self.relations






