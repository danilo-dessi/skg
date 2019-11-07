import pandas as pd
import random


def count_source(triple2source, source_label):
	return sum([1 for (s, p, o) in triple2source if source_label in triple2source[(s,p,o)]])

def get_cso_topics():
	cso_topics = []
	with open('../../resources/CSO.3.1.csv', 'r', encoding='utf-8') as f:
		lines = f.readlines()
		for line in lines:
			triple = line.strip().split(',')

			if "\"<https://cso.kmi.open.ac.uk/topics/" in triple[0]:
				e = triple[0].replace("\"<https://cso.kmi.open.ac.uk/topics/", "")
				e = e[:-2]
				
				cso_topics += [e]

			if "\"<https://cso.kmi.open.ac.uk/topics/" in triple[2]:
				e = triple[2].replace("\"<https://cso.kmi.open.ac.uk/topics/", "")
				e = e[:-2]
				cso_topics += [e]
			
	cso_topics = set(cso_topics)
	return set(cso_topics)


def get_sw_children():
	sw_children = []
	with open('sw_children.txt', 'r') as f:
		lines = f.readlines()
		sw_children = [ e.strip() for e in lines ]
	return sw_children


def get_extended_entities():
	hold_entities = []
	with open('hold_entities.txt', 'r') as f:
		lines = f.readlines()
		hold_entities = [ e.strip() for e in lines ]
	return hold_entities


def select_sw_cso(triple2source, triple2support):
	cso_topics = get_cso_topics()
	sw_children = get_sw_children()
	hold_entities = get_extended_entities()
	
	sw_triple2source = {}
	sw_triple2support = {}

	for (s, p, o)  in triple2source:
		if (s in sw_children and (o.replace(' ', '_') in cso_topics or o in hold_entities)) or ((s.replace(' ', '_') in cso_topics or s  in hold_entities)  and o in sw_children):
			#triples_sw += [(s, p, o, source, support)]
			if (s,p,o) not in sw_triple2source:
				sw_triple2source[(s,p,o)] = triple2source[(s,p,o)]
				sw_triple2support[s,p,o] = triple2support[(s,p,o)]
	return sw_triple2source, sw_triple2support


#used just once to retrieve old annotations
def retrieve_old_annotations(filename, column):
	data_triples = pd.read_csv(filename, sep=';')
	triples = {}
	for i, row in data_triples.iterrows():
		s = row['s']
		p = row['p']
		o = row['o']
		annotation = row[column]
		triples[(s,p,o)] = annotation
	return triples




def save(triple2source, triple2support, pipeline, filename):

	Danilo_old_annotations = retrieve_old_annotations('selected_sw_triples_20_09_2019_annotated_danilo_fra.csv', 'Danilo')
	for (s,p,o) in triple2source:
		if (s,p,o) not in Danilo_old_annotations:
			Danilo_old_annotations[(s,p,o)] = ''

	Fra_old_annotations = retrieve_old_annotations('selected_sw_triples_20_09_2019_annotated_danilo_fra.csv', 'FRA')
	for (s,p,o) in triple2source:
		if (s,p,o) not in Fra_old_annotations:
			Fra_old_annotations[(s,p,o)] = ''
	

	#print('Annotations: ',len(old_annotations), len(triple2source))

	columns_order = ['s', 'p', 'o', 'source', 'support', 'pipeline', 'Danilo', 'FRA']
	data = [{'s' : s, 'p' : p, 'o' : o, 'source' : triple2source[(s,p,o)], 'support' : triple2support[(s,p,o)], 'pipeline' : pipeline[(s,p,o)], 'Danilo': Danilo_old_annotations[(s,p,o)], 'FRA':Fra_old_annotations[(s,p,o)] } for (s,p,o) in triple2source if s != o]
	df = pd.DataFrame(data, columns=columns_order)
	df = df[columns_order]
	df.to_csv(filename, sep=';')



def load_triples(filename):
	data_triples = pd.read_csv(filename, sep=';')

	triple2source = {}
	triple2support = {}
	for i, row in data_triples.iterrows():
		s = row['s']
		p = row['p']
		o = row['o']
		source = row['source']
		support = row['support']
		if p != 'conjunction' and s != o: 
			if (s,p,o) not in triple2source:
				triple2source[(s,p,o)] = [source]
				triple2support[(s,p,o)] = [support]
			else:
				triple2source[(s,p,o)] += [source]
				triple2support[(s,p,o)] += [support]
	return triple2source, triple2support



if __name__ == "__main__":


	th_support = 5
	triple2source, triple2support = load_triples('selected_triples_01_10.csv')
	dis_triple2source, dis_triple2support = load_triples('discarded_triples_01_10.csv')

	print('Number of relations', len(triple2source))
	print('Number of relations from Luan Yi et al\'s tool', count_source(triple2source, 'luanyi'))
	print('Number of relations from OpenIE', count_source(triple2source, 'openie'))
	print('Number of relations from our Heuristic', count_source(triple2source, 'heuristic'))

	triples2source_high = {}
	for (s, p, o) in triple2source:
		if 'heuristic' in triple2source[(s,p,o)]:
			pos_support = triple2source[(s,p,o)].index('heuristic')
			support = triple2support[(s,p,o)][pos_support]
			if support >= th_support:
				triples2source_high[(s,p,o)] = triple2source[(s,p,o)]
	print('Number of relations from our Heuristic with high support', count_source(triples2source_high, 'heuristic'))


	# SW
	sw_triple2source, sw_triple2support = select_sw_cso(triple2source, triple2support)
	print('\nNumber of relations with SW filters', len(sw_triple2source))
	print('Number of relations from Luan Yi et al\'s tool in SW triples', count_source(sw_triple2source, 'luanyi'))
	print('Number of relations from OpenIE in SW triple', count_source(sw_triple2source, 'openie'))
	print('Number of relations from our Heuristic in SW triple', count_source(sw_triple2source, 'heuristic'))
	sw_triples2source_high = {}
	for (s, p, o) in sw_triple2source:
		if 'heuristic' in sw_triple2source[(s,p,o)]:
			pos_support = sw_triple2source[(s,p,o)].index('heuristic')
			support = sw_triple2support[(s,p,o)][pos_support]
			if support >= th_support:
				sw_triples2source_high[(s,p,o)] = sw_triple2source[(s,p,o)]
	print('Number of relations from our Heuristic with high support', count_source(sw_triples2source_high, 'heuristic'))
	
	pipeline = {(s,p,o) : 'yes' for (s,p,o) in sw_triple2source}


	#dis_triple2source, dis_triple2support = load_triples('discarded_triples.csv')
	dis_sw_triple2source, dis_sw_triple2support = select_sw_cso(dis_triple2source, dis_triple2support)
	tmp = []
	for (s,p,o) in dis_sw_triple2support:
		if dis_sw_triple2support[(s,p,o)][0] >= 3:
			tmp += [(s,p,o)]

	dis_sw_triple2source = { (s,p,o) : dis_sw_triple2source[(s,p,o)] for (s,p,o) in tmp if (s,p,o) not in sw_triple2source}
	dis_sw_triple2support = { (s,p,o) : dis_sw_triple2support[(s,p,o)] for (s,p,o) in tmp if (s,p,o) not in sw_triple2support}

	for (s,p,o) in dis_sw_triple2source:
		if (s,p,o) not in pipeline:
			pipeline[(s,p,o)] = 'no'


	sw_triple2source.update(dis_sw_triple2source)
	sw_triple2support.update(dis_sw_triple2support)



	print('\nNumber of relations with SW filters', len(sw_triple2source))
	print('Number of relations from Luan Yi et al\'s tool in SW triples', count_source(sw_triple2source, 'luanyi'))
	print('Number of relations from OpenIE in SW triple', count_source(sw_triple2source, 'openie'))
	print('Number of relations from our Heuristic in SW triple', count_source(sw_triple2source, 'heuristic'))
	sw_triples2source_high = {}
	for (s, p, o) in sw_triple2source:
		if 'heuristic' in sw_triple2source[(s,p,o)]:
			pos_support = sw_triple2source[(s,p,o)].index('heuristic')
			support = sw_triple2support[(s,p,o)][pos_support]
			if support >= th_support:
				sw_triples2source_high[(s,p,o)] = sw_triple2source[(s,p,o)]
	print('Number of relations from our Heuristic with high support', count_source(sw_triples2source_high, 'heuristic'))



	#save(sw_triple2source, sw_triple2support, pipeline,'gs_sw_triples_to_annotate.csv')
	



















