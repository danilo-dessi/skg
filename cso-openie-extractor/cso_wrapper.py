#from cso_classifier_master.classifier import classifier as CSO 
import classifier.classifier as CSO


class CSO_wrapper:
	def __init__(self):
		self.text = ''

	def __find_str(self, s, char):
		index = 0
		if char in s:
			c = char[0]
			for ch in s:
				if ch == c:
					if s[index : index + len(char)] == char:
						return index
				index += 1
		return -1

	def apply(self, text):
		paper = {
		"title": "",
		"abstract": text,
		"keywords": ""
		}
	
		result = CSO.run_cso_classifier(paper, modules = "both", enhancement = "first")
		entities = {}
		errors = {}
		for e in result['union']:
			start_index = self.__find_str(text, e)
			if start_index != -1:
				entities[e] = {'start' : start_index, 'end' : start_index + len(e)}
			else:
				errors[e] = {'start' : start_index, 'end' : start_index + len(e)}

		return entities




if __name__ == '__main__':
	t = """ "Operators of online social networks are increasingly sharing potentially "
		"sensitive information about users and their relationships with advertisers, application "
		"developers, and data-mining researchers. Privacy is typically protected by anonymization, "
		"i.e., removing names, addresses, etc. We present a framework for analyzing privacy and "
		"anonymity in social networks and develop a new re-identification algorithm targeting "
		"anonymized social-network graphs. To demonstrate its effectiveness on real-world networks, "
		"we show that a third of the users who can be verified to have accounts on both Twitter, a "
		"popular microblogging service, and Flickr, an online photo-sharing site, can be re-identified "
		"in the anonymous Twitter graph with only a 12% error rate. Our de-anonymization algorithm is "
		"based purely on the network topology, does not require creation of a large number of dummy "
		"\"sybil\" nodes, is robust to noise and all existing defenses, and works even when the overlap "
		"between the target network and the adversary's auxiliary information is small." """
	c = CSO_wrapper()
	e = c.apply(t)

	print(e)



