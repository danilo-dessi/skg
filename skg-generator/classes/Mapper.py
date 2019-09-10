import pandas as pd
import urllib

class Mapper:

	def __init__(self, triples):
		self.triples = triples
		self.hold_relations = ['used-for', 'hyponym-of', 'part-of', 'feature-of', 'conjuction', 'RELATE', 'evaluate-for']

	def verb_mapper(self):
		verb_taxonomy = pd.read_csv('resources/SKG_predicates.csv', sep=';')
		#print(verb_taxonomy.head(5))
		vMap = {}
		vCount = {}
		for i, r in verb_taxonomy.iterrows():
			to_ = r['predicate-simplified']
			for j in range(14):
				index = 'v' + str(j)
				from_ = r[index]
				vMap[from_]  = to_
				vCount[to_] = 0

		triple_verb_mapped = []
		lost = 0
		lost_triples = []
		for (s, p_start, o, source, support) in self.triples:
			p = self.solve_auxiliar_verbs(p_start)
			if p in vMap:
				triple_verb_mapped += [(s, vMap[p], o, source, support)]
				vCount[vMap[p]] += 1
			elif p in self.hold_relations:
				triple_verb_mapped += [(s, p, o, source, support)]
			else:
				#print('LOST BECAUSE VERB', (s, p, o, source, support) )
				lost_triples += [(s, p, o, source, support)]
				#print('LOST:',(s, p, o, source, support), p_start, p)
				lost += 1
		
		self.triples = triple_verb_mapped
		print('Lost count:', lost)

		columns_order = ['s', 'p', 'o', 'source', 'support']
		data = [{'s' : s, 'p' : p, 'o' : o, 'source' : source, 'support' : support} for (s,p,o, source, support) in lost_triples]
		df = pd.DataFrame(data, columns=columns_order)
		df = df[columns_order]
		df.to_csv('out/lost_triples.csv')

		# used-for management
		triples_tmp = []
		for (s, p, o, source, support) in self.triples:
			if p == 'used-for':
				print((s,p,o, source, support))
				print((o, 'uses', s, source, support), '\n')
				triples_tmp += [(o, 'uses', s, source, support)]
			else:
				triples_tmp += [(s, p, o, source, support)]
		self.triples = triples_tmp

		# feature-of management
		triples_tmp = []
		for (s, p, o, source, support) in self.triples:
			if p == 'feature-of' or p == 'part-of':
				print((s,p,o, source, support))
				print((o, 'includes', s, source, support), '\n')
				triples_tmp += [(o, 'includes', s, source, support)]
			else:
				triples_tmp += [(s, p, o, source, support)]
		self.triples = triples_tmp

		# evaluate-for management
		triples_tmp = []
		for (s, p, o, source, support) in self.triples:
			if p == 'evaluate-for':
				print((s,p,o, source, support))
				print((s, 'evaluates', o, source, support), '\n')
				triples_tmp += [(s, 'evaluates', o, source, support)]
			else:
				triples_tmp += [(s, p, o, source, support)]
		self.triples = triples_tmp



	def load_cso_triples(self):
		triples = []
		with open('resources/CSO.3.1.csv', 'r', encoding="utf-8") as f:
			lines = f.readlines()
			for line in lines:

				try:
					(s,p,o) = tuple(line.strip().split(','))
					(s,p,o) = (urllib.parse.unquote(s[1:-1]), urllib.parse.unquote(p[1:-1]), urllib.parse.unquote(o[1:-1]))
					triples += [ (s,p,o)]
				except Exception as e:
					pass

		return triples


	def equivalentSet(self, cso_triples, entity):

		entity = entity.replace(' ', '_')
		equivalent_set = []
		for triple in cso_triples:
			
			if "<http://cso.kmi.open.ac.uk/schema/cso#relatedEquivalent>" == triple[1] and \
				"<https://cso.kmi.open.ac.uk/topics/" + entity + ">" == triple[0]:
				
				obj = triple[2].split('/')[-1] # last part 
				obj = obj[:-1] 		   # > remotion
				equivalent_set += [obj]

		equivalent_set += [entity]
		equivalent_set = sorted(equivalent_set, key=len, reverse=True)
		equivalent_set = [e.replace('_', ' ') for e in  equivalent_set]

		return equivalent_set
	

	def equivalentMap(self, triples_plain):
		eMap = {'xslt' : 'extensible stylesheet language (xslt)', 
		        'cbr' : 'content based recommendation (cbr)',
		        'ehr' : 'electronic health record (ehr)',
		        'crm' : 'conceptual reference model (crm)',
		        'cim' : 'computation independent model (cim)',
		        'cad' : 'computer aided design (cad)',
		        'vhdl' : 'very high speed integrated circuit description language (vhdl)',
		        'xml' : 'extensible markup language (xml)',
		        'sql' : 'structured query language (sql)',
		        'ict' : 'information communications technology (ict)',
		        'dicom' : 'digital imaging and communication in medicine (dicom)',
		        'http' : 'hypertext transfer protocol (http)',
		        'ssd' : 'semantic service description (ssd)',
		        'wsn' : 'wireless sensor networks (wsn)',
		        'html' : 'hypertext markup language (html)',
		        'pim' : 'product information model (pim)',
		        'spin' : 'sparql inferencing notation (spin)',
		        'scorm' : 'sharable content object reference model (scorm)',
		        'bpmn' : 'business process modeling notation (bpmn)',
		        'fca' : 'formal concept analysis (fca)',
		        'vsm' : 'vector space model (vsm)',
		        'ahp' : 'analytic hierarchy process (ahp)',
		        'dht' : 'distributed hash tables (dht)',
		        'ber' : 'bit error rate (ber)',
		        'bpm' : 'business process modeling (bpm)',
		        'ogc' : 'open geospatial consortium (ogc)',
		        'csp' : 'communicating sequential processes (csp)',
		        'cac' : 'congenial access control (cac)',
		        'dht' : 'distributed hash table',
		        'cbir' : 'content based image retrieval (cbir)',
		        'fso' : 'financial statement ontology (fso)',
		        'cam' : 'complementary and alternative medicines (cam)',
		        'etl' : 'extract-transform-load (etl) process',
		        'soc' : 'service-oriented computing (soc)',
		        'datum' : 'data',
		        'linked open datum' : 'linked open data',
		        'lod datum' : 'lod data',
		        'linked datum' : 'linked data',
		        'calendar datum' : 'calendar data',
		        'structured datum' : 'structured data',
		        'semantic datum' : 'semantic data'}

		cso_triples = self.load_cso_triples()

		for (s,p,o) in triples_plain:

			if s not in eMap:
				equivalent_set = self.equivalentSet(cso_triples, s)
				for e in equivalent_set:
					eMap[e] = equivalent_set[0]	

			if s not in eMap:
				eMap[s] = s

			if o not in eMap:
				equivalent_set = self.equivalentSet(cso_triples, o)
				for e in equivalent_set:
					eMap[e] = equivalent_set[0]

			if o not in eMap:
				eMap[o] = o
				
		return eMap
	


	def entities_mapper(self):

		print('Building entity mapping with CSO')
		triples_plain = [(s,p,o) for (s,p,o, source, support) in self.triples]
		eMap = self.equivalentMap(triples_plain)

		#print('COUNT:', len(self.triples))
		triples_mapped = []
		for (s,p,o, source, support) in self.triples:
			new_s = s
			new_o = o 

			if s in eMap:
				new_s = eMap[s]
			if o in eMap:
				new_o = eMap[o]
			triples_mapped += [(new_s, p, new_o, source, support)]

		self.triples =  triples_mapped


	def solve_auxiliar_verbs(self, p):
		
			if p.startswith('can '):
				return p.replace('can ', '')
			elif p.startswith('may '):
				return p.replace('may ', '')
			elif p.startswith('might '):
				return p.replace('might ', '')
			elif p.startswith('will '):
				return p.replace('will ', '')
			elif p.startswith('have '):
				return p.replace('have ', '')
			elif p.startswith('has '):
				return p.replace('has ', '')
			elif p.startswith('be '):
				return p.replace('be ', '')
			elif p.startswith('should '):
				return p.replace('should ', '')
			else:
				return p




	def save(self, filename):
		columns_order = ['s', 'p', 'o', 'source', 'support']
		data = [{'s' : s, 'p' : p, 'o' : o, 'source' : source, 'support' : support} for (s,p,o, source, support) in self.triples]
		df = pd.DataFrame(data, columns=columns_order)
		df = df[columns_order]
		df.to_csv(filename)

	def get_triples(self):
		return self.triples


	def run(self):
		print('Number before mapping:', len(self.triples))

		self.verb_mapper()
		print('Number after verb mapping:', len(self.triples))

		self.entities_mapper()
		print('Number after entities mapping:', len(self.triples))

		self.triples = set(self.triples)





