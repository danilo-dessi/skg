
import networkx as nx
import csv
from urllib.parse import unquote


class RelationsBuilder:

	def __init__(self, g):
		self.g = g
		self.label2node = {}
		self.node2label = {}
		self.relations = {}
		self.csoResourcePath = 'resources/CSO.3.1.csv'
		self.csoTopics = set()
		self.csoTriples = set()


	def loadGraphData(self):
		for edge in self.g.edges():
			self.relations[edge] = self.g.edges[edge]['label']

		for node in self.g.nodes():
			label = self.g.nodes[node]['label']
			self.label2node[label] = node
			self.node2label[node] = label


	def loadCSO(self):
		t1_ok = False
		t2_ok = False
		with open(self.csoResourcePath) as csv_file:
			csv_reader = csv.reader(csv_file, delimiter=',')
			for row in csv_reader:
				#print(row)
				t1 = unquote(row[0])[1:-1]
				t2 = unquote(row[2])[1:-1]

				if t1.startswith('https://cso.kmi.open.ac.uk/topics/'):
					t1 = t1.split('/')[-1]
					self.csoTopics.add(t1.lower())
					t1_ok = True

				if t2.startswith('https://cso.kmi.open.ac.uk/topics/'):
					t2 = t2.split('/')[-1]
					self.csoTopics.add(t2.lower())
					t2_ok = True

				if t1_ok and t2_ok:
					r = unquote(row[1])
					self.csoTriples.add((t1.lower(), r, t2.lower()))
					

				t1_ok = False
				t2_ok = False	
		print('Number of CSO topics:', len(self.csoTopics))

	def findSubTopics(self):
		generics = {}

		for label in self.label2node:
			keyLabel = label.replace(' ', '_')
			generics[label] = []
			if label in self.csoTopics:
				for triple in self.csoTriples:
					if triple[0] == label and triple[1] == '<http://cso.kmi.open.ac.uk/schema/cso#superTopicOf>':
						generics[label] += [triple[2]]
		return generics


	def addRelations(self, subEntity, upEntity):

		subEntityNode = self.label2node[subEntity]
		upEntityNode = self.label2node[upEntity]
		inEdges = self.g.in_edges(subEntityNode)
		outEdges = self.g.out_edges(subEntityNode)

		newEdges = {}
		newEdgesWeight = {}

		for edge in inEdges:
			neighborNode = edge[0]
			if (neighborNode, upEntityNode) not in self.g.edges():
				newEdges[(neighborNode, upEntityNode)] = self.g.edges[edge]['label']
				print('neighbor -> supertopic',(self.node2label[neighborNode], self.g.edges[edge]['label'], upEntity))
			
		for edge in outEdges:
			neighborNode = edge[1]
			if (upEntityNode, neighborNode) not in self.g.edges():
				newEdges[(upEntityNode, neighborNode)] = self.g.edges[edge]['label']
				print('supertopic -> neighbor',(upEntity, self.g.edges[edge]['label'], self.node2label[neighborNode]))
			
		for edge in newEdges:
			if edge not in self.g.edges():
				self.g.add_edge(edge[0], edge[1], label=newEdges[edge], weight=100)


			

	def buildRelations(self):
		superTopic2SubTopics = self.findSubTopics()
		for upTopic in superTopic2SubTopics:
			subTopics = superTopic2SubTopics[upTopic]
			for subTopic in subTopics:
				if subTopic.replace('_', ' ') in self.label2node:
					self.addRelations(subTopic.replace('_', ' '), upTopic.replace('_', ' '))

	
	def get_g(self):
		return self.g


	def run(self):
		self.loadCSO()
		self.loadGraphData()
		self.buildRelations()
		


if __name__ == '__main__':
	g = nx.read_graphml('../kg.graphml')
	c = RelationsBuilder(g)
	c.run()
