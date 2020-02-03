import os
import subprocess
import pandas as pd

if not os.path.exists('./csv_e_r'):
	os.mkdir('./csv_e_r')


seed = 'miachiave'
for file in os.listdir('./data/processed_data/json/luanyi_input/'):
	print(file)
	
	fi = open('generate_elmo.py', 'r')
	generate_elmo_string = fi.read()
	generate_elmo_string = generate_elmo_string.replace(seed, file.replace('.json',''))
	fi.close()
	fo = open('generate_elmo.py', 'w')
	fo.write(generate_elmo_string)
	fo.flush()
	fo.close()

	command = ['python', 'generate_elmo.py']
	p = subprocess.Popen(command)
	out, err = p.communicate()
	p.wait()

	fi = open('experiments.conf', 'r')
	experiments_string = fi.read()
	experiments_string = experiments_string.replace(seed, file.replace('.json',''))
	fi.close()
	fo = open('experiments.conf', 'w')
	fo.write(experiments_string)
	fo.flush()
	fo.close()


	fi = open('lsgn_evaluator.py', 'r')
	lsgn = fi.read()
	lsgn = lsgn.replace(seed, file.replace('.json',''))
	fi.close()
	fo = open('lsgn_evaluator.py', 'w')
	fo.write(lsgn)
	fo.flush()
	fo.close()

	command = ['python', 'evaluator.py', 'scientific_best_ner']
	p = subprocess.Popen(command)
	out, err = p.communicate()
	p.wait()


	command = ['rm data/processed_data/elmo/luanyi_input/*']
	p = subprocess.Popen(command)
	out, err = p.communicate()
	p.wait()

	
	seed = file.replace('.hdf5','')
	print(seed)


fi = open('generate_elmo.py', 'r')
generate_elmo_string = fi.read()
generate_elmo_string = generate_elmo_string.replace(seed, 'miachiave')
fi.close()
fo = open('generate_elmo.py', 'w')
fo.write(generate_elmo_string)
fo.flush()
fo.close()

fi = open('experiments.conf', 'r')
experiments_string = fi.read()
experiments_string = experiments_string.replace(seed, 'miachiave')
fi.close()
fo = open('experiments.conf', 'w')
fo.write(experiments_string)
fo.flush()
fo.close()


fi = open('lsgn_evaluator.py', 'r')
lsgn = fi.read()
lsgn = lsgn.replace(seed, 'miachiave')
fi.close()
fo = open('lsgn_evaluator.py', 'w')
fo.write(lsgn)
fo.flush()
fo.close()


#save all in a single file

dir = 'csv_e_r/'
files = os.listdir(dir)

data = None

for file in files:
	print(file)
	if data is None:
		data = pd.read_csv(dir + file)
	else:	
		temp = pd.read_csv(dir + file)
		data = pd.concat([data, temp])
data.to_csv('../luanyi_output.csv')


