import pandas as pd
import sklearn as sk
import requests
import rdflib
import time
import ast 
import string 
import json
import numpy as np
import operator
from sklearn.feature_extraction.text import TfidfVectorizer
from stanfordcorenlp import StanfordCoreNLP
from nltk.tokenize import sent_tokenize
import nltk
import numpy as np
import re
import os
import sys
import datetime
import json


def parse_mag_json(json_file_directory):

	ids = []
	titles = []
	abstracts = []
	dois = []
	keywords = []

	for file in os.listdir(json_file_directory):
		if '.json' in file:
			with open(json_file_directory + '/' + file, 'r') as f:
				content = f.read()
				myjson = json.loads(content)
				print(file)
				for hit in myjson['hits']['hits']:
					if hit['_score'] > 7.5:
						try:
							source = hit['_source']

							if 'title' in source:
								title = source['title']
							else:
								title = ''

							if 'abstract' in source:
								abstract = source['abstract']
							else:
								abstract = ''

							if 'id' in source:
								id = source['id']
							else:
								id = ''

							if 'doi' in source:
								doi = source['doi']
							else:
								doi = ''

							if 'keywords' in source:
								keyword = source['keywords']
							else:
								keyword = []

							ids += [id]
							titles += [title]
							abstracts += [abstract]
							dois += [doi]
							keywords += [keyword]

						except:
							pass

	data = {'id' : ids, 'title' : titles, 'abstract' : abstracts, 'keywords' : keywords, 'doi' : dois }
	df = pd.DataFrame.from_dict(data)
	df.to_csv('data.csv')


def prepare_for_luanyi(df, name):
	regex = re.compile(r"^[a-zA-Z0-9][A-Za-z0-9 _-]+")

	i = 0
	for row_id, values in df[['abstract', 'id']].iterrows():
		i += 1
	
		abstract = values['abstract']

		if not isinstance(abstract, float):
			text = abstract
			paper_id = values['id']

			printable = set(string.printable)
			cleaned_string = ''.join(list(filter(lambda x: x in printable, text)))
			all_sentences = sent_tokenize(cleaned_string)


			sentences  = []
			ner = []
			clusters = []
			relations = []
			
			for s in all_sentences:
				s_cleaned = re.sub("[^a-zA-Z0-9 ]", '', s)
				sentences += [nltk.word_tokenize(s)]
				clusters += [[]]
				ner += [[]]
				relations += [[]]

			abstract_json = {}
			abstract_json['clusters'] = clusters
			abstract_json['sentences'] = sentences
			abstract_json['ner'] = ner
			abstract_json['relations'] = relations
			abstract_json['doc_key'] = str(paper_id) 

			with open(name + '_input_luanyi.json', 'a') as fp:
				json.dump(abstract_json, fp)
				fp.write("\n")	
	


if __name__ == '__main__':

	json_file_directory = 'mag_data' # the directory that contains the MAG json files
	file = 'file.csv'       		 # a csv that is produced with the MAG data and that contains all abstracts of input data
	n_splits = 20					 # the Luanyi et al. tool raises problems on big data, therefore, we split data to be fed to the tool 


	#parsing
	parse_mag_json(json_file_directory)

	# input for Luanyi tool
	directory = 'luanyi_input_dir'
	if not os.path.exists(directory):
		os.makedirs(directory)

	data = pd.read_csv(file)
	subdata = np.array_split(data, n_splits)
	for i in range(len(subdata)):
		print(i, str(datetime.datetime.now()))
		prepare_for_luanyi(subdata[i], directory + '/' + file.split('.')[0] + '_' + str(i))

	# creation of textual resource that will be subsequently employed in the pipeline
	data = pd.read_csv(file)
	with open('all_abstracts.txt', 'w+') as f:
		for abstract in data['abstract']:
			f.write(abstract.strip() + '\n')

	print('DONE')
