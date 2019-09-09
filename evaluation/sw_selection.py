import pandas as pd


def save(triples, filename):
	columns_order = ['s', 'p', 'o', 'source', 'support']
	data = [{'s' : s, 'p' : p, 'o' : o, 'source' : source, 'support' : support} for (s,p,o, source, support) in triples]
	df = pd.DataFrame(data, columns=columns_order)
	df = df[columns_order]
	df.to_csv(filename)

def filter_with_cso(triples, cso_topics, sw_children):
	triples_filtered = []
	for (s, p, o, source, support) in triples:
		if  (s in sw_children and o.replace(' ', '_') in cso_topics ) or (s.replace(' ', '_') in cso_topics and o in sw_children):
			triples_filtered += [(s, p, o, source, support)]
	return triples_filtered

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
	return cso_topics


def get_sw_children():
	sw_children = []
	
	with open('sw_children.txt', 'r') as f:
		lines = f.readlines()
		sw_children = [ e.strip() for e in lines ]
	return sw_children



if __name__ == '__main__':

	full_data = pd.read_csv('../../out/all_triples.csv', sep=',')
	triples = []
	for i, row in full_data.iterrows():
		s = row['s']
		p = row['p']
		o = row['o']
		source = row['source']
		support = row['support']
		triples += [(s, p, o, source, support)]

	print('Load cso topics')
	cso_topics = get_cso_topics()

	print('Load sw topics')
	sw_children = get_sw_children()

	all_sw = filter_with_cso(triples, cso_topics, sw_children)

	print('Select only Luanyi relations')
	triples_luanyi = [(s, p, o, source, support) for (s, p, o, source, support) in triples if source == 'luanyi']
	triples_luanyi_sw = filter_with_cso(triples_luanyi, cso_topics, sw_children)
	print(triples_luanyi_sw)
	exit(1)

	print('Select only Openie relations')
	triples_openie = [(s, p, o, source, support) for (s, p, o, source, support) in triples if source == 'openie']
	triples_openie_sw = filter_with_cso(triples_openie, cso_topics, sw_children)

	print('Select only Window relations')
	triples_window = [(s, p, o, source, support) for (s, p, o, source, support) in triples if source == 'heuristic']
	triples_window_sw = filter_with_cso(triples_window, cso_topics, sw_children)

	print('Select triples with high support')
	th = 9
	triples_trusted_sw = [(s, p, o, source, support) for (s, p, o, source, support) in triples_luanyi_sw + triples_openie_sw  + triples_window_sw if support >= th]
	

	
	selected_triples = pd.read_csv('../../out/selected_triples.csv', sep=',')
	final_triples = []
	for i, row in full_data.iterrows():
		s = row['s']
		p = row['p']
		o = row['o']
		source = row['source']
		support = row['support']
		final_triples += [(s, p, o, source, support)]
	final_triples_sw = filter_with_cso(final_triples, cso_topics, sw_children)

	save(all_sw, '0-all_sw.csv')
	save(set(triples_luanyi_sw), '1-luanyi_sw.csv')
	print('Luanyi:', len(set(triples_luanyi_sw)))
	print('Luanyi high support:', set([(s,p,o) for (s, p, o, source, support) in triples_luanyi_sw if support >= th]))

	save(set(triples_openie_sw), '2-openie_sw.csv')
	print('Openie:', len(set(triples_openie_sw)))
	print('Openie high support:', set([(s,p,o) for (s, p, o, source, support) in triples_openie_sw if support >= th]))

	save(set(triples_window_sw), '3-heuristic_sw.csv')
	print('Window:', len(set(triples_window_sw)))
	print('Window high support:', set([(s,p,o) for (s, p, o, source, support) in triples_window_sw if support >= th]))

	save(set(triples_trusted_sw), '4-trusted_sw.csv')
	print('Trusted:', len(set(triples_trusted_sw)))

	save(set(final_triples_sw), '5-trusted_consistent.csv')
	print('Final:', len(set(final_triples_sw)))


	spo = set([(s,p,o) for (s, p, o, source, support) in final_triples])
	columns_order = ['s', 'p', 'o']
	data = [{'s' : s, 'p' : p, 'o' : o} for (s,p,o) in spo]
	df = pd.DataFrame(data, columns=columns_order)
	df = df[columns_order]
	df.to_csv('triples_clean.csv')

	









