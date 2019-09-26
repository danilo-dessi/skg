import pandas as pd 


data = pd.read_csv('selected_triples_20_09_2019.csv', sep=';')
print(data.describe())


data = data[data['p'] != 'conjunction']
print(data.describe())

data = data[data['s'] != data['o']]
print(data.describe())

data.to_csv('selected_triples_20_09_2019_no_conj.csv')




















