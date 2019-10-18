import networkx as nx
import sys
import os


def findSubgraph(gname, e):

	g = nx.read_graphml(gname)

	node = -1
	for n in g.nodes():
		if g.nodes[n]['label'] == e:
			node = n
			break

	if node != -1:
		neighbors = [neighbor for neighbor in g.neighbors(node)	]
		subg = g.subgraph([node] + neighbors)
		nx.write_graphml(subg, './subgraphs/' + e + '__subg.graphml')
		print('Saved:', subg, './subgraphs/' + e + '__subg.graphml')
	else:
		print("'" + e + "' is not present in the graph " + gname)


if __name__ == '__main__':

	if not os.path.exists('./subgraphs'):
		os.makedirs('./subgraphs')

	findSubgraph(sys.argv[1], sys.argv[2])


