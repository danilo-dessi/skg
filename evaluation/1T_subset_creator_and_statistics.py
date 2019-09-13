import pandas as pd
import random


def count_source(triples, source_label):
	return sum([1 for (s, p, o, source, support) in triples if source == source_label])

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



def select_sw_cso(triples):
	cso_topics = get_cso_topics()
	sw_children = get_sw_children()

	triples_sw = []

	for (s, p, o, source, support)  in triples:

		if (s in sw_children and o.replace(' ', '_') in cso_topics) or (s.replace(' ', '_') in cso_topics and o in sw_children):
			triples_sw += [(s, p, o, source, support)]
	return triples_sw





def save(triples, filename):
	columns_order = ['s', 'p', 'o', 'source', 'support']
	data = [{'s' : s, 'p' : p, 'o' : o, 'source' : source, 'support' : support} for (s,p,o, source, support) in triples]
	df = pd.DataFrame(data, columns=columns_order)
	df = df[columns_order]
	df.to_csv(filename)


if __name__ == "__main__":
	data_triples = pd.read_csv('selected_triples.csv')


	triples = []
	for i, row in data_triples.iterrows():
		s = row['s']
		p = row['p']
		o = row['o']
		source = row['source']
		support = row['support']
		triples += [(s, p, o, source, support)]
	
	print('Read', len(triples), 'triples')
	

	print('Number of relations', len(triples))
	print('Number of relations from Luan Yi et al\'s tool', count_source(triples, 'luanyi'))
	print('Number of relations from OpenIE', count_source(triples, 'openie'))
	print('Number of relations from our Heuristic', count_source(triples, 'heuristic'))
	print('Number of relations from our Heuristic with high support', count_source([(s, p, o, source, support)  for (s, p, o, source, support) in triples if support >= 9], 'heuristic'))

	random.shuffle(triples)
	random.shuffle(triples)
	random.shuffle(triples)
	random.shuffle(triples)

	triples_1T = triples[:1000]
	print('\nNumber of relations from Luan Yi et al\'s tool in 1T triples', count_source(triples_1T, 'luanyi'))
	print('Number of relations from OpenIE in 1T triples', count_source(triples_1T, 'openie'))
	print('Number of relations from our Heuristic in 1T triples', count_source(triples_1T, 'heuristic'))
	print('Number of relations from our Heuristic with high support in 1T triples', count_source([(s, p, o, source, support)  for (s, p, o, source, support) in triples_1T if support >= 9], 'heuristic'))

	save(triples_1T, 'triples_1T.csv')


	triples_sw = select_sw_cso(triples)
	print('\nNumber of relations with SW filters', len(triples_sw))
	print('Number of relations from Luan Yi et al\'s tool in SW triples', count_source(triples_sw, 'luanyi'))
	print('Number of relations from OpenIE in SW triple', count_source(triples_sw, 'openie'))
	print('Number of relations from our Heuristic in SW triple', count_source(triples_sw, 'heuristic'))
	print('Number of relations from our Heuristic with high support in SW triple', count_source([(s, p, o, source, support)  for (s, p, o, source, support) in triples_sw if support >= 9], 'heuristic'))

	random.shuffle(triples_sw)
	random.shuffle(triples_sw)
	random.shuffle(triples_sw)
	random.shuffle(triples_sw)

	triples_1T = triples_sw[:1000]
	print('\nNumber of relations from Luan Yi et al\'s tool in 1T SW triples', count_source(triples_1T, 'luanyi'))
	print('Number of relations from OpenIE in 1T SW triples', count_source(triples_1T, 'openie'))
	print('Number of relations from our Heuristic in 1T SW triples', count_source(triples_1T, 'heuristic'))
	print('Number of relations from our Heuristic with high support in 1T SW triples', count_source([(s, p, o, source, support)  for (s, p, o, source, support) in triples_1T if support >= 9], 'heuristic'))

	save(triples_1T, 'triples_sw_1T.csv')



















