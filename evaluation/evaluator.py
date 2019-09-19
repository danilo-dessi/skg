import pandas as pd 
import ast


def load_triples_ann(filename, ann_name):
	triples = {}
	data = pd.read_csv(filename, sep=';')
	for i, r in data.iterrows():
		if r['p'] != 'conjunction':
			triples[(r['s'], r['p'], r['o'])] = r[ann_name]
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
	triples2ann = load_triples_ann('selected_sw_triples_annotated_new.csv', 'Danilo')
	triples2source = load_triples_ann('selected_sw_triples_annotated_new.csv', 'source')
	triples2support = load_triples_ann('selected_sw_triples_annotated_new.csv', 'support')
	triples2pipeline = load_triples_ann('selected_sw_triples_annotated_new.csv', 'pipeline')


	luanyi_triples = [t for t in triples2source if 'luanyi' in triples2source[t] and triples2pipeline[t] == 'yes']
	openie_triples = [t for t in triples2source if 'openie' in triples2source[t] and triples2pipeline[t] == 'yes']
	heuristic_triples = [t for t in triples2source if 'heuristic' in triples2source[t] and triples2pipeline[t] == 'yes']
	heuristic_triples_high = [t for t in heuristic_triples if ast.literal_eval(triples2support[t])[ast.literal_eval(triples2source[t]).index('heuristic')] >= 9]
	allpipeline_triples = [t for t in triples2source if triples2pipeline[t] == 'yes']
	nopipeline_triples = [t for t in triples2source if triples2pipeline[t] == 'no']


	print('Number of Luan Yi triples:\t\t', len(luanyi_triples))
	print('Number of OpenIE triples:\t\t', len(openie_triples))
	print('Number of Heuristic triples:\t\t', len(heuristic_triples))
	print('Number of Heuristic high support triples:', len(heuristic_triples_high))
	print('Number of all pipeline triples:\t\t', len(allpipeline_triples))
	print('Number of no pipeline triples:\t\t', len(nopipeline_triples))
	print()

	p,r,f = precision_recall(luanyi_triples, triples2ann)
	print('Luan Yi \t- \tPrecision:', p, 'Recall:', r, 'F1:', f)

	p,r,f = precision_recall(openie_triples, triples2ann)
	print('OpenIE \t\t- \tPrecision:', p, 'Recall:', r, 'F1:', f)

	p,r,f = precision_recall(heuristic_triples_high, triples2ann)
	print('Heuristic High \t- \tPrecision:', p, 'Recall:', r, 'F1:', f)

	p,r,f = precision_recall(heuristic_triples, triples2ann)
	print('Heuristic \t- \tPrecision:', p, 'Recall:', r, 'F1:', f)

	p,r,f = precision_recall(allpipeline_triples, triples2ann)
	print('General \t- \tPrecision:', p, 'Recall:', r, 'F1:', f)
	








