'''
This file contains functions that can be used to compute the frequencies of entities 
on two different datasets of abstracts. 
The first dataset is a dataset of abstracts and keywords of a given domain.
The second dataset is made of abstracts and keywords of papers that do not belong to the domain of the first dataset.
The user must specify a keyword that identifies a domain (e.g. Semantic Web, Bioinformatics etc.)
The dataset are built runtime from MAG dataset and have a comparable size.

The result is composed a pandas with the frequency for each entities across the datasets.

'''

import networkx as nx
import pandas as pd
from elasticsearch import Elasticsearch 
import string
import re
import os
import csv
import nltk
from nltk.stem.lancaster import LancasterStemmer
from nltk.stem import WordNetLemmatizer



def retrieveEntities(g):
	nodes = g.nodes()
	entities = []
	for node in nodes:
		entities += [g.nodes[node]['label']]
	return entities


def loadData(file):
	data = []
	with open(file, 'r') as f:
		data = f.readlines()
	data = [x.lower().replace('\n', ' ') for x in data]
	return data


def loadDataAbstract(file):
	data = []
	with open(file, 'r') as f:
		data = f.readlines()
	
	regex = re.compile('[%s]' % re.escape(string.punctuation))
	data = [regex.sub(' ', x.lower().replace('-\n', '').replace('\n', ' ')) for x in data]
	return data


def keywordsValidation(allKeywordsDomain, entities):
	validEntities = []
	allKeywordsDomainSet = set([x[:-1] for x in allKeywordsDomain])
	for e in entities:
		if e in allKeywordsDomainSet:
			validEntities += [e]
	return set(validEntities)


def loadCSODictionary():

	csoDictionary = []
	with open('ComputerScienceOntology_v2.csv', 'r') as csvfile:
		reader = csv.reader(csvfile, delimiter=';')
		for row in reader:
			csoDictionary += [row[0]]
	return csoDictionary

def csoValidation(csoDictionary, entities):
	validEntities = []
	for e in entities:
		if e in csoDictionary:
			validEntities += [e]
	return set(validEntities)



def computeOccurrenciesOnAbstracts(entities, allAbstractsDomain, allAbstractsOtherDomain, allAbstractsComputerScience, fileStatName):
	cds = []
	cos = []
	ccs = []
	regex = re.compile('[%s]' % re.escape(string.punctuation))

	for e in entities:
		print(e)
		cd = sum([str(' ' + abstract + ' ').count( str(' ' + regex.sub(' ', e) + ' ')) for abstract in allAbstractsDomain]) + 1
		cds += [cd]
		
		co = sum([str(' ' + abstract + ' ').count(str(' ' + regex.sub(' ', e) + ' ')) for abstract in allAbstractsOtherDomain]) + 1
		cos += [co]

		co = sum([str(' ' + abstract + ' ').count(str(' ' + regex.sub(' ', e) + ' ')) for abstract in allAbstractsComputerScience]) + 1
		ccs += [co]

	stats = pd.DataFrame({'entity' : entities, 'domain-count' : cds, 'other-domains-count' : cos, 'computer-science-count' : ccs})
	stats = stats.sort_values('domain-count', ascending=False)
	stats.to_csv(fileStatName)
	


def getVerbs(textString):

	wordnet_lemmatizer = WordNetLemmatizer()

	verbs = []
	text = nltk.word_tokenize(textString)
	poss = nltk.pos_tag(text)
	for pos in poss:
		if pos[1].startswith('VB'):
			verb = wordnet_lemmatizer.lemmatize(pos[0], 'v') 
			verbs += [verb]
	return verbs


def computeVerbsOccurrenciesOnAbstracts(allAbstractsDomain, allAbstractsOtherDomain, allAbstractsComputerScience):

	verbCount = {}
	for a in allAbstractsDomain:
		verbs = getVerbs(a)
		for verb in verbs:
			if verb not in verbCount:
				verbCount[verb] = {'domain-count' : 1}
				verbCount[verb]['other-domains-count'] = 1
				verbCount[verb]['computer-science-count'] = 1
			verbCount[verb]['domain-count'] += 1 

	
	for a in allAbstractsOtherDomain:
		verbs = getVerbs(a)
		for verb in verbs:
			if verb not in verbCount:
				verbCount[verb] = {'domain-count' : 1}
				verbCount[verb]['other-domains-count'] = 1
				verbCount[verb]['computer-science-count'] = 1
			verbCount[verb]['other-domains-count'] += 1 


	for a in allAbstractsComputerScience:
		verbs = getVerbs(a)
		for verb in verbs:
			if verb not in verbCount:
				verbCount[verb] = {'domain-count' : 1}
				verbCount[verb]['other-domains-count'] = 1
				verbCount[verb]['computer-science-count'] = 1
			verbCount[verb]['computer-science-count'] += 1 

	verbs = []
	cds = []
	cos = []
	ccs = []
	freq1 = []
	freq2 = []
	for verb in verbCount:
		verbs += [verb]
		cds += [verbCount[verb]['domain-count']]
		cos += [verbCount[verb]['other-domains-count']]
		ccs += [verbCount[verb]['computer-science-count']]
		freq1 += [verbCount[verb]['domain-count'] / verbCount[verb]['other-domains-count']]
		freq2 += [verbCount[verb]['domain-count'] / verbCount[verb]['computer-science-count']]

	stats = pd.DataFrame({'verb' : verbs, 'domain-count' : cds, 'other-domains-count' : cos, 'computer-science-count' : ccs})
	stats = stats.sort_values('domain-count', ascending=False)
	stats.to_csv('statsVerb.csv')
	return verbCount



def loadStats(fileStatName):
	data = pd.read_csv(fileStatName)
	entities = data['entity'].tolist()
	cds = data['domain-count'].tolist()
	cos = data['other-domains-count'].tolist()
	ccs = data['computer-science-count'].tolist()

	entityStats = {}
	for i in range(len(entities)):
		entityStats[entities[i]] = {'domain' : float(cds[i])}
		entityStats[entities[i]] ['otherDomain'] = float(cos[i])
		entityStats[entities[i]] ['computerScience'] = float(ccs[i])
		entityStats[entities[i]]['domainOnOtherDomain'] = float(cds[i]) / float(cos[i])
		entityStats[entities[i]]['domainOnComputerScience'] = float(cds[i]) / float(ccs[i])

	return entityStats


def statsValidation(entityStats, entities, thSWCS, thSWGEN):
	validEntities = []
	for e in entities:
		if entityStats[e]['domainOnOtherDomain'] >= thSWGEN and entityStats[e]['domainOnComputerScience'] >= thSWCS:
			validEntities += [e]
	return set(validEntities)



def cleanGraph(g, validEntities):
	nodesIDs = []
	nodes = list(g.nodes())
	for node in nodes:
		if g.nodes[node]['label'] in validEntities:
			nodesIDs += [node]
	return g.subgraph(nodesIDs)


def cleanGraphByTriples(g, thTriple):
	edges = g.edges()
	edgesToRemove = []
	for edge in edges:
		if g.edges[edge]['weight'] < thTriple:
			edgesToRemove += [edge]
	print('N edges to remove:', len(edgesToRemove), '/', len(edges))
	g = nx.DiGraph(g)
	g.remove_edges_from(edgesToRemove)
	return g




if __name__ == '__main__':
	graphPath = 'semantic_web_workshop_new.graphml'
	graphOutPath = graphPath.replace('.graphml','_cleaned.graphml')
	thSWCS = 2
	thSWGEN = 3
	thTriple = 2

	g = nx.read_graphml(graphPath)

	entities = retrieveEntities(g)
	print('Number of entities:', len(entities))


	allAbstractsDomain = loadDataAbstract('datasets/allAbstractsDomain.txt')
	allKeywordsDomain = loadData('datasets/allKeywordsDomain.txt')
	allTitlesDomain = loadData('datasets/allTitlesDomain.txt')

	allAbstractsOtherDomain = loadDataAbstract('datasets/allAbstractsOtherDomain.txt')
	allKeywordsOtherDomain = loadData('datasets/allKeywordsOtherDomain.txt')
	allTitlesOtherDomain = loadData('datasets/allTitlesOtherDomain.txt')

	allAbstractsComputerScience = loadDataAbstract('datasets/allAbstractsComputerScience.txt')
	allKeywordsComputerScience = loadData('datasets/allKeywordsComputerScience.txt')
	allTitlesComputerScience = loadData('datasets/allTitlesComputerScience.txt')

	#statsVerb = computeVerbsOccurrenciesOnAbstracts(allAbstractsDomain, allAbstractsOtherDomain, allAbstractsComputerScience)
	#exit(1)

	keywordsValidatedEntities = keywordsValidation(allKeywordsDomain, entities)
	print("Entities validated with keywords:", len(keywordsValidatedEntities))

	csoDictionary = loadCSODictionary()
	csoValidatedEntitis = csoValidation(csoDictionary, entities)
	print("Entities validated with cso:", len(csoValidatedEntitis))
	
	fileStatName = 'stats_' + graphPath.replace('.graphml', '.csv')
	if os.path.exists(fileStatName):
		entityStats = loadStats(fileStatName)
	else:
		computeOccurrenciesOnAbstracts(entities, allAbstractsDomain, allAbstractsOtherDomain, allAbstractsComputerScience, fileStatName)
		entityStats = loadStats(fileStatName)

	
	statsValidatedEntities = statsValidation(entityStats, entities, thSWCS, thSWGEN)
	print("Entities validated with statistics:", len(statsValidatedEntities))

	validEntities = keywordsValidatedEntities | csoValidatedEntitis | statsValidatedEntities
	print('All validated entities:', len(validEntities))

	gCleaned = nx.DiGraph(cleanGraph(g, validEntities))
	#gCleaned = cleanGraphByTriples(gCleaned, thTriple)
	
	isolated_nodes = [n for n,d in gCleaned.degree() if d == 0]
	gCleaned.remove_nodes_from(isolated_nodes)
	nx.write_graphml(gCleaned, graphOutPath)

	print('Nodes:', len(gCleaned.nodes()), 'Edges:', len(gCleaned.edges()))






	
	
	

























