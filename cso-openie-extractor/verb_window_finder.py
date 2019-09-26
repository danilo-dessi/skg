import nltk
from nltk.stem import WordNetLemmatizer
from itertools import combinations 
from gensim.models.keyedvectors import KeyedVectors
import numpy as np
from scipy import spatial
import random
import spacy
from spacy.lang.en import LEMMA_INDEX, LEMMA_EXC, LEMMA_RULES
import datetime
import sys
import csv
import gc
from stanfordcorenlp import StanfordCoreNLP
import json



class VerbWindowFinder:

	def __init__(self, nlp):
		self.window = 20
		self.spacy_nlp = spacy.load('en_core_web_sm')
		self.lemmatizer = spacy.lemmatizer.Lemmatizer(LEMMA_INDEX, LEMMA_EXC, LEMMA_RULES) 
		self.corenlp = nlp

		
	def findSubList(self, sl,l):
	    results = []
	    sll = len(sl)
	    for ind in (i for i, e in enumerate(l) if e == sl[0]):
	        if l[ind : ind + sll] == sl:
	            results.append((ind, ind + sll - 1))
	    return results

	def findVerbs(self, textTags, posE1, posE2):
		verbs = []
		verbs_tags = []
		i = posE1[1] + 1
		end = posE2[0]

		subjectDistance = None
		objectDistance = None

		while i < end:
			if (textTags[i][1].startswith('VB')):
				j = i
				verb = []
				verb_tags = []
				for j in range(i, len(textTags)):
					if (textTags[j][1].startswith('VB')):

						verb += [textTags[j][0]]
						verb_tags += [textTags[j][1]]
						if subjectDistance == None:
							subjectDistance = i - posE1[1] # current position minus subject last token position
						i += 1

					elif (textTags[j][1].startswith('RB')): #adverbs 
						i += 1

					else:
						if objectDistance == None:
							objectDistance = end - i # object first token position minus current position
						verbs += [verb]
						verbs_tags += [verb_tags]
						break
			i += 1
		return verbs, verbs_tags

	def isPassive(self, verb, verb_tags):#isPassive(self, verb, wordnet_lemmatizer):
		return len(verb) >= 2 and self.spacy_lemmatizer(verb[-2], 'v') == 'be' and verb_tags[-1] == 'VBN'



	def spacy_lemmatizer(self, word, pos_tag):
		lemma = sorted(self.lemmatizer(word, pos_tag))[0]
		return lemma


	def runCoreNLP(self, text):
		corenlp_out = None
		props = {'annotators': 'tokenize,pos,lemma,depparse', 'pipelineLanguage': 'en', 'outputFormat': 'json'}
		try:
			corenlp_out = json.loads(self.corenlp.annotate(text, properties=props))
		except Exception as e:
			print('Stanford Core NLP is not responding. Please try later')
			print(e)
			exit(1)
		return corenlp_out


	def getCoreNLPTokens(self, coreNLPparsing):
		textTokens = []
		for sentence in coreNLPparsing['sentences']:
			for token in sentence['tokens']:
				textTokens += [token['word']]
		return textTokens


	def getCoreNLPTags(self, coreNLPparsing):
		textTags = []
		for sentence in coreNLPparsing['sentences']:
			for token in sentence['tokens']:
				textTags += [(token['word'], token['pos'])]
		return textTags


	def getSentenceComplexity(self, coreNLPparsing):
		return len(coreNLPparsing['sentences'][0]['basicDependencies'])



	def run(self, text, entities):
		
		sentence_text = text
		sentence_entities = entities
		coreNLPparsing = self.runCoreNLP(sentence_text)
		textTokens = self.getCoreNLPTokens(coreNLPparsing)
		textTags = self.getCoreNLPTags(coreNLPparsing)

		entitiesComb = [(s,o) for (s,o) in combinations(set(sentence_entities), 2)]
		entitiesCombTokenized = [(self.runCoreNLP(s), self.runCoreNLP(o)) for (s,o) in entitiesComb]
		entitiesCombTokenized = [(self.getCoreNLPTokens(s_coreNLPparsing), self.getCoreNLPTokens(o_coreNLPparsing)) for (s_coreNLPparsing,o_coreNLPparsing) in entitiesCombTokenized]
			
		new_sentence_relations = []

		for k in range(len(entitiesComb)):
			rel = entitiesComb[k]
			relTokenized = entitiesCombTokenized[k]
			sTokens = relTokenized[0]
			oTokens = relTokenized[1]

			# finding of positions of subject and object tokens
			sPos = self.findSubList(sTokens, textTokens)
			oPos = self.findSubList(oTokens, textTokens)


			for spos in sPos:
				for opos in oPos:
					if spos[1] - opos[0] < 0 and abs(spos[1] - opos[0]) <= self.window:
						
						if abs(spos[1] - opos[0]) == 2 and (textTokens[spos[1] + 1] == ',' or textTokens[spos[1] + 1] == 'and'):
							new_sentence_relations += [(rel[0], 'RELATE', rel[1])]
							new_sentence_relations += [(rel[1], 'RELATE', rel[0])]
				
						verbs, verbs_tags = self.findVerbs(textTags, spos, opos)
						for vi in range(len(verbs)):
							verb = verbs[vi]
							verb_tags = verbs_tags[vi]
							rnew = None
							if not self.isPassive(verb, verb_tags):
								rnew = (rel[0], self.spacy_lemmatizer(verb[-1], u"VERB"), rel[1])		
							else:
								rnew = (rel[1], self.spacy_lemmatizer(verb[-1], u"VERB"), rel[0])

							new_sentence_relations += [rnew]
					

					elif opos[1] - spos[0] < 0 and abs(opos[1] - spos[0]) <= self.window:
						if abs(opos[1] - spos[0]) == 2 and (textTokens[opos[1] + 1] == ',' or textTokens[opos[1] + 1] == 'and'):
							new_sentence_relations += [(rel[0], 'RELATE', rel[1])]
							new_sentence_relations += [(rel[1], 'RELATE', rel[0])]
				
						verbs, verbs_tags= self.findVerbs(textTags, opos, spos)
						for vi in range(len(verbs)):
							verb = verbs[vi]
							verb_tags = verbs_tags[vi]
							rnew = None
							if not self.isPassive(verb, verb_tags):
								rnew = (rel[1], self.spacy_lemmatizer(verb[-1], u"VERB"), rel[0])
							else:	
								rnew = (rel[0], self.spacy_lemmatizer(verb[-1], u"VERB"), rel[1])

							new_sentence_relations += [rnew]

		final_sentence_relations = []
		for (s,p,o) in new_sentence_relations:
			final_sentence_relations += [(s, 'verb_window-' + p, o)]

		return final_sentence_relations

