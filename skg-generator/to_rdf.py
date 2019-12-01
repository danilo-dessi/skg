from rdflib import Graph, URIRef,  Literal
from urllib.parse import unquote
import pandas as pd
import csv

triples_dataframe = pd.read_csv('triples.csv', sep=';')



#loading CSO
csoTopics = set()
with open('resources/CSO.3.1.csv', 'r', encoding='utf-8') as csv_file:
	csv_reader = csv.reader(csv_file, delimiter=',')
	for row in csv_reader:
		t1 = unquote(row[0]).replace('<https://', '')[:-1]
		t2 = unquote(row[2]).replace('<https://', '')[:-1]
		if t1.startswith('cso.kmi.open.ac.uk/topics/'):
			t1 = t1.split('/')[-1]
			csoTopics.add(t1.lower())
		if t2.startswith('cso.kmi.open.ac.uk/topics/'):
			t2 = t2.split('/')[-1]
			csoTopics.add(t2.lower())


# retrieving of generated triples from the dataframe
triples = []
for i, row in triples_dataframe.iterrows():
	
	s = row['s'].strip().replace(' ', '_')
	p = row['p']
	o = row['o'].strip().replace(' ', '_')
	triples += [(s,p,o)]


# RDF generation
cso_namespace = 'https://cso.kmi.open.ac.uk/topics/'
swkg_namespace = 'https://swkg.kmi.open.ac.uk/entity/'
relation_namespace = 'https://swkg.kmi.open.ac.uk/relation/'
g = Graph()

for (s,p,o) in triples:

	s_URI = ''
	if s in csoTopics:
		s_URI = URIRef(cso_namespace + s)
	else:
		s_URI = URIRef(swkg_namespace + s)

	o_URI = ''
	if s in csoTopics:
		o_URI = URIRef(cso_namespace + o)
	else:
		o_URI = URIRef(swkg_namespace + o)

	p_URI = URIRef(relation_namespace + p)

	g.add((s_URI, p_URI, o_URI))

print(g.serialize( "SemWebKG.rdf", format="xml"))
print(g.serialize( "SemWebKG.nt", format="nt"))













