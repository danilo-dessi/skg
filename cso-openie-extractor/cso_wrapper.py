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






