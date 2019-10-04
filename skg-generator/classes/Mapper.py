import pandas as pd
import urllib

class Mapper:

	def __init__(self, triples):
		self.triples = triples
		self.hold_relations = ['used-for', 'hyponym-of', 'part-of', 'feature-of', 'conjuction', 'RELATE', 'evaluate-for']

	def verb_mapper(self):
		verb_taxonomy = pd.read_csv('resources/SKG_predicates.csv', sep=';')
		
		vMap = {}
		vCount = {}
		for i, r in verb_taxonomy.iterrows():
			to_ = r['predicate-simplified']
			for j in range(14):
				index = 'v' + str(j)
				from_ = r[index]
				vMap[from_]  = to_

		triple_verb_mapped = []
		lost = 0
		lost_triples = []
		for (s, p_start, o, source, support) in self.triples:
			p = self.solve_auxiliar_verbs(p_start)
			if p in vMap:
				triple_verb_mapped += [(s, vMap[p], o, source, support)]
				#vCount[vMap[p]] += 1
			elif p in self.hold_relations:
				triple_verb_mapped += [(s, p, o, source, support)]
			else:
				#print('LOST BECAUSE VERB', (s, p, o, source, support))
				lost_triples += [(s, p, o, source, support)]
				lost += 1
		
		self.triples = triple_verb_mapped
		print('Lost count:', lost)

		columns_order = ['s', 'p', 'o', 'source', 'support']
		data = [{'s' : s, 'p' : p, 'o' : o, 'source' : source, 'support' : support} for (s,p,o, source, support) in lost_triples]
		df = pd.DataFrame(data, columns=columns_order)
		df = df[columns_order]
		df.to_csv('out/lost_triples.csv')

		# Luan Yi triples management
		triples_tmp = []
		for (s, p, o, source, support) in self.triples:
			if p == 'used-for':
				#print((s,p,o, source, support))
				#print((o, 'uses', s, source, support), '\n')
				triples_tmp += [(o, 'uses', s, source, support)]
			elif p == 'feature-of' or p == 'part-of':
				#print((s,p,o, source, support))
				#print((o, 'includes', s, source, support), '\n')
				triples_tmp += [(o, 'includes', s, source, support)]
			elif p == 'evaluate-for':
				#print((s,p,o, source, support))
				#print((s, 'evaluates', o, source, support), '\n')
				triples_tmp += [(s, 'evaluates', o, source, support)]
			else:
				triples_tmp += [(s, p, o, source, support)]
		self.triples = triples_tmp


	def entities_mapper(self):

		#print('Building entity mapping with CSO')
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


	def get_triples(self):
		return self.triples


	def map_on_definitive_predicates(self):
		verb_taxonomy = pd.read_csv('resources/SKG_predicates.csv', sep=';')
		vMap = {}

		for i, r in verb_taxonomy.iterrows():
			vMap[r['predicate-simplified']] = r['predicate']

		final_triples = []
		for (s,p,o,source,support) in self.triples:
			final_triples += [(s, vMap[p], o, source, support)]

		self.triples = final_triples



	def run(self):
		print('Number before mapping:', len(self.triples))

		self.verb_mapper()
		print('Number after verb mapping:', len(self.triples))

		self.triples = set(self.triples)





