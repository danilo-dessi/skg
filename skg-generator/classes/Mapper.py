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
		for (s, p_start, o, source, support, abstracts) in self.triples:
			p = self.solve_auxiliar_verbs(p_start)
			if p in vMap:
				triple_verb_mapped += [(s, vMap[p], o, source, support, abstracts)]
				#vCount[vMap[p]] += 1
			elif p in self.hold_relations:
				triple_verb_mapped += [(s, p, o, source, support, abstracts)]
			else:
				#print('LOST BECAUSE VERB', (s, p, o, source, support))
				lost_triples += [(s, p, o, source, support, abstracts)]
				lost += 1
		
		self.triples = triple_verb_mapped

		print('Lost count:', lost)

		columns_order = ['s', 'p', 'o', 'source', 'support']
		data = [{'s' : s, 'p' : p, 'o' : o, 'source' : source, 'support' : support, 'abstracts' : abstracts} for (s,p,o, source, support, abstracts) in lost_triples]
		df = pd.DataFrame(data, columns=columns_order)
		df = df[columns_order]
		df.to_csv('out/lost_triples.csv')

		# Luan Yi triples management
		triples_tmp = []
		for (s, p, o, source, support, abstracts) in self.triples:
			if p == 'used-for':
				triples_tmp += [(o, 'uses', s, source, support, abstracts)]

			elif p == 'feature-of' or p == 'part-of':
				triples_tmp += [(o, 'includes', s, source, support, abstracts)]

			elif p == 'evaluate-for':
				triples_tmp += [(s, 'evaluates', o, source, support, abstracts)]

			else:
				triples_tmp += [(s, p, o, source, support, abstracts)]

		self.triples = triples_tmp



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
		for (s,p,o,source,support, abstracts) in self.triples:
			final_triples += [(s, vMap[p], o, source, support, abstracts)]
		self.triples = final_triples


	def run(self):
		print('Number before mapping:', len(self.triples))

		self.verb_mapper()
		print('Number after verb mapping:', len(self.triples))





