import pandas as pd 
import ast

def load_triples(filename):
	data_triples = pd.read_csv(filename, sep=',')

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
				triple2support[s,p,o] = [support]
			else:
				triple2source[(s,p,o)] += [source]
				triple2support[s,p,o] += [support]
	return triple2source, triple2support


def count_source(triple2source, source_label):
	s =  sum([1 for (s, p, o) in triple2source if source_label in triple2source[(s,p,o)]])
	rel = [(s, p, o) for (s, p, o) in triple2source if source_label in triple2source[(s,p,o)]]
	return rel, s


if __name__ == "__main__":

	th_support = 20
	triple2source, triple2support = load_triples('all_triples.csv')
	print(len(triple2source.keys()))
	

	c = 0
	for t in triple2source:
		
		if 'heuristic' in triple2source[t]:
			i = triple2source[t].index('heuristic')
			if triple2support[t][i] >= 5:
				print(t, triple2support[t], triple2source[t])
				c += 1
	print(c)
	exit(1)

	
	rel_luanyi, c_luanyi = count_source(triple2source, 'luanyi')
	rel_openie, c_openie = count_source(triple2source, 'openie')
	rel_heuristic, c_heuristic = count_source(triple2source, 'heuristic')

	print('Number of relations', len(triple2source))
	print('Number of relations from Luan Yi et al\'s tool', c_luanyi)
	print('Number of relations from OpenIE', c_openie)
	print('Number of relations from our Heuristic', c_heuristic)

	print('Number of relations in common Luan Yi and OpenIE', len(set(rel_luanyi).intersection(set(rel_openie))))
	print('Number of relations in common OpenIE and Heuristic', len(set(rel_openie).intersection(set(rel_heuristic))))
	print('Number of relations in common Luan Yi and Heuristic', len(set(rel_luanyi).intersection(set(rel_heuristic))))
	print('Number of relations in common between all', len(set(rel_luanyi).intersection(set(rel_heuristic)).intersection(set(rel_openie))))





