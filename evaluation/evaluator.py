import pandas as pd 



def load_triples_ann(filename, ann_name):
	triples = {}
	data = pd.read_csv(filename, sep=';')
	for i, r in data.iterrows():
		if r['p'] != 'conjunction':
			triples[(r['s'], r['p'], r['o'])] = r[ann_name]
	#print(len(triples))
	return triples



def precision_recall(triples, gs_triples):

	tp = 0
	tn = 0
	fp = 0
	fn = 0
	for t in gs_triples:
		if t in triples and gs_triples[t] == 'y':
			tp += 1
		elif  t not in triples and gs_triples[t] == 'n':
			tn += 1
		elif t in triples and gs_triples[t] == 'n':
			fp += 1
		elif t not in triples and gs_triples[t] == 'y':
			fn += 1

	p = tp / (tp + fp)
	r = tp / (tp + fn)
	f = 2 * (p * r) / (p + r)

	return p, r , f



if __name__ == "__main__":
	triples2ann = load_triples_ann('selected_sw_triples_ann.csv', 'Danilo')
	triples2source = load_triples_ann('selected_sw_triples_ann.csv', 'source')
	triples2support = load_triples_ann('selected_sw_triples_ann.csv', 'support')

	luanyi_triples = [t for t in triples2source if triples2source[t] == 'luanyi']
	openie_triples = [t for t in triples2source if triples2source[t] == 'openie']
	heuristic_triples = [t for t in triples2source if triples2source[t] == 'heuristic']
	heuristic_triples_high = [t for t in triples2source if triples2source[t] == 'heuristic' and triples2support[t] >= 9]

	p,r,f = precision_recall(luanyi_triples, triples2ann)
	print('Luan Yi \t- \tPrecision:', p, 'Recall:', r, 'F1:', f)

	p,r,f = precision_recall(openie_triples, triples2ann)
	print('OpenIE \t\t- \tPrecision:', p, 'Recall:', r, 'F1:', f)

	p,r,f = precision_recall(heuristic_triples_high, triples2ann)
	print('Heuristic High \t- \tPrecision:', p, 'Recall:', r, 'F1:', f)

	p,r,f = precision_recall(heuristic_triples, triples2ann)
	print('Heuristic \t- \tPrecision:', p, 'Recall:', r, 'F1:', f)

	p,r,f = precision_recall(triples2ann, triples2ann)
	print('General \t- \tPrecision:', p, 'Recall:', r, 'F1:', f)
	








