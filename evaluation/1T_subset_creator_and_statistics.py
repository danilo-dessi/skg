import pandas as pd
import random


def count_source(triples, source_label):
	return sum([1 for (s, p, o, source, support) in triples if source == source_label])

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


