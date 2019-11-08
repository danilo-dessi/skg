import pandas as pd 
import ast
from matplotlib import pyplot as plt

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
	file = 'gs_sw_triples_01_10_definitive.csv'
	triples2ann = load_triples_ann(file, 'Majority-vote')
	triples2source = load_triples_ann(file, 'source')
	triples2support = load_triples_ann(file, 'support')
	triples2pipeline = load_triples_ann(file, 'pipeline')

	luanyi_triples = [t for t in triples2source if 'luanyi' in triples2source[t] and triples2pipeline[t] == 'yes']
	openie_triples = [t for t in triples2source if 'openie' in triples2source[t] and triples2pipeline[t] == 'yes']
	heuristic_triples = [t for t in triples2source if 'heuristic' in triples2source[t] and triples2pipeline[t] == 'yes']


	heuristic_triples_low = []
	for t in heuristic_triples:

		tsources = ast.literal_eval(triples2source[t])
		#print(tsources)
		indices = [i for i, x in enumerate(tsources) if x == "heuristic"]
		tsupports = ast.literal_eval(triples2support[t])
		#print(tsupports)
		support = max([tsupports[i] for i in indices])
		#print(support)
		if support < 10:
			heuristic_triples_low += [t]

	#heuristic_triples_high = [t for t in heuristic_triples if ast.literal_eval(triples2support[t])[ast.literal_eval(triples2source[t]).index('heuristic')] >= 20]
	allpipeline_triples = [t for t in triples2source if triples2pipeline[t] == 'yes']
	nopipeline_triples = [t for t in triples2source if triples2pipeline[t] == 'no']

	print('Heuristic:\t\t', len(heuristic_triples))
	print('Heuristic (low support only):', len(heuristic_triples_low))

	'''
	x = []
	y = []
	for i in range(1,50):
		ti = []
		for t in heuristic_triples:
			#print(t, triples2support[t])
			tsources = ast.literal_eval(triples2source[t])

			indices = [i for i, x in enumerate(tsources) if x == "heuristic"]
			tsupports = ast.literal_eval(triples2support[t])
	
			support = max([tsupports[i] for i in indices])

			if support >= i:
				ti += [t]
		p,r,f = precision_recall(ti, triples2ann)
		
		x += [i]
		y += [p]
		print('Support >=', i , 'triples:', len(ti), 'p:', p, 'r:', r, 'f:', f)
		if i == 45 or i == 46:
			for triple in ti:
				print(triple)
	'''

	x = []
	y = []
	for i in range(1,100):
		ti = []
		for t in allpipeline_triples:
			
			tsupports = ast.literal_eval(triples2support[t])
			support = max(tsupports)

			if support >= i:
				ti += [t]
		p,r,f = precision_recall(ti, triples2ann)
		
		x += [i]
		y += [p]
		print('Support >=', i , 'triples:', len(ti), 'p:', p, 'r:', r, 'f:', f)
		
plt.plot(x, y)
# naming the x axis 
plt.xlabel('support') 
# naming the y axis 
plt.ylabel('precision') 
plt.ylim(0.7, 1.01)
plt.axvline(x=10, color='k', linestyle='--')
plt.show()





