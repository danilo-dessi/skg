
import networkx as nx
import csv
from urllib.parse import unquote


class RelationsBuilder:

	def __init__(self, g):
		self.g = g
		self.label2node = {}
		self.node2label = {}
		self.relations = {}
		self.csoResourcePath = '../resources/CSO.3.1.csv'
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
		with open(self.csoResourcePath) as csv_file:
			csv_reader = csv.reader(csv_file, delimiter=',')
			for row in csv_reader:
				#print(row)
				t1 = unquote(row[0]).replace('<https://', '')[:-1]
				t2 = unquote(row[2]).replace('<https://', '')[:-1]
				t1 = t1.split('/')[-1]
				t2 = t2.split('/')[-1]
				r = unquote(row[1])
				self.csoTriples.add((t1.lower(), r, t2.lower()))
				self.csoTopics.add(t1.lower())
				self.csoTopics.add(t2.lower())


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

		#print('UP:', upEntity, 'SUB:', subEntity)
		#print('NodeUP:', upEntityNode, 'NodeSUB:', subEntityNode)
		#print('IN EDGES:', inEdges)
		#print('OUT EDGES:', outEdges)
		#exit(1)



		for edge in inEdges:
			neighborNode = edge[0]
			if (neighborNode, upEntityNode) not in self.g.edges():
				#print('NEW relation:', self.node2label[neighborNode], '-', self.g.edges[edge]['label'], '-',  self.node2label[upEntityNode])
				#print('ORIGINAL', self.node2label[neighborNode], '-', self.g.edges[edge]['label'], '-',  self.node2label[subEntityNode], '\n')
				newEdges[(neighborNode, upEntityNode)] = self.g.edges[edge]['label']
			#else:
				#print('OLD relation:', self.node2label[neighborNode], '-', self.g.edges[edge]['label'], '-',  self.node2label[upEntityNode], '\n')


		for edge in outEdges:
			neighborNode = edge[1]
			if (upEntityNode, neighborNode) not in self.g.edges():
				#print('NEW relation:', self.node2label[upEntityNode], '-', self.g.edges[edge]['label'], '-',  self.node2label[neighborNode])
				#print('ORIGINAL', self.node2label[subEntityNode], '-', self.g.edges[edge]['label'], '-', self.node2label[neighborNode], '\n')
				newEdges[(upEntityNode, neighborNode)] = self.g.edges[edge]['label']
			#else:
				#print('OLD relation:', self.node2label[neighborNode], '-', self.g.edges[edge]['label'], '-',  self.node2label[upEntityNode], '\n')

		for edge in newEdges:
			if edge not in self.g.edges():
				self.g.add_edge(edge[0], edge[1], label='INFER-' + newEdges[edge], weight=100)
			

	def buildRelations(self):
		superTopic2SubTopics = self.findSubTopics()
		
		for upTopic in superTopic2SubTopics:
			subTopics = superTopic2SubTopics[upTopic]
			for subTopic in subTopics:
				if subTopic in self.label2node:
					self.addRelations(subTopic, upTopic)

	
	def run(self):
		self.loadCSO()
		self.loadGraphData()
		self.buildRelations()
		


if __name__ == '__main__':
	g = nx.read_graphml('../out/semantic_web.graphml')
	c = RelationsBuilder(g)
	c.run()
