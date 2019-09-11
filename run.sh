
# Stanford Core NLP download
wget http://nlp.stanford.edu/software/stanford-corenlp-full-2018-10-05.zip
unzip stanford-corenlp-full-2018-10-05.zip
rm stanford-corenlp-full-2018-10-05.zip


# Luan Yi e al 's tool download
wget https://bitbucket.org/luanyi/scierc/get/a8f486a9c1b4.zip
unzip a8f486a9c1b4.zip
rm a8f486a9c1b4.zip
mv luanyi-scierc-a8f486a9c1b4 master
cp -r master/ luanyi-extractor/
rm -r master

cd luanyi-extractor
cd master
./scripts/fetch_required_data.sh
./scripts/build_custom_kernels.sh
wget http://nlp.cs.washington.edu/sciIE/models/scientific_best_ner.zip
unzip scientific_best_ner.zip
rm scientific_best_ner.zip
cp ../use/requirements.txt ./
pip install -r requirements.txt

# this is a time consuming task
python generate_elmo.py

# this task does not stop. The user has to force its stop by interrupting the process
echo "Keep this process running for a while (5 minutes is enough)"
echo "then stop it with ctrl+c (only once). See the Luan Yi et al.'s repository for details about this behavior of singleton.py"
python singleton.py scientific_best_ner
python evaluator.py scientific_best_ner

echo "The Luan Yi et al.'s tool has been configured"



# data preparation
cd ../data-preparation
python3 parse_input.py


#Luan Yi et al's tool execution
cd ../luanyi-extractor/
cp -r ../data-preparation/luanyi_input ./master/data/processed_data/json/
mkdir ./master/data/processed_data/elmo/luanyi_input
cp use/* master/*
cd master
python generate_elmo.py
python3 run.py


# CSO and OpenIE extraction
cd ../cso-openie-extractor
cp ../luanyi-extractor/luanyi_output.cs ./
python3 run.py


# Towards the skg
cd ../skg-generator
#wget archive    
cp ../cso-openie-extractor/csv_e_r_full.csv ./
python3 run.py















