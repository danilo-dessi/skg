import pandas as pd 

'''data = pd.read_csv('selected_triples_20_09_2019.csv', sep=';')
print(data.describe())


data = data[data['p'] != 'conjunction']
print(data.describe())

data = data[data['s'] != data['o']]
print(data.describe())

data.to_csv('selected_triples_20_09_2019_no_conj.csv')'''



data = pd.read_csv('selected_sw_triples_20_09_2019_annotated_danilo_fra.csv', sep=';')
triples = []
for i, r in data.iterrows():
	triples += [(r['s'], r['p'], r['o'], r['source'], r['support'], r['pipeline'])]



verb_taxonomy = pd.read_csv('../skg-generator/resources/SKG_predicates.csv', sep=';')
vMap = {}

for i, r in verb_taxonomy.iterrows():
	vMap[r['predicate-simplified']] = r['predicate']

final_triples = []
data_to_save = []
for (s,p,o,source,support, pipeline) in triples:
	final_triples += [(s, vMap[p], o, source, support, pipeline)]
	print((s,p,o,source,support) , '\n', (s, vMap[p], o, source, support, pipeline), '\n')
	data_to_save += [{'s' : s, 'p' : vMap[p], 'o' : o, 'source' : source, 'support' : support, 'pipeline' : pipeline}]

columns_order = ['s', 'p', 'o', 'source', 'support', 'pipeline']
df = pd.DataFrame(data_to_save, columns=columns_order)
df = df[columns_order]
df.to_csv('selected_sw_triples_to_annotate.csv', sep=';')






















