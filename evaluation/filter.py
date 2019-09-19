import pandas as pd

data = pd.read_csv('selected_sw_triples_annotated.csv', sep=';')
print(data.describe())
data = data[data['s'] != data['o']]
print(data.describe())
data.to_csv('selected_sw_triples_annotated_new.csv', sep=';')
