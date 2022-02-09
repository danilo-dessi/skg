# Scientific Knowledge Graph Generator



This repository contains the source code developed to build a hybrid architecture generates a Scientific Knowledge Graph about the Semantic Web domain. The results of this research work have been published in: 

This work has been described in:
```
Dessì, D., Osborne, F., Recupero, D. R., Buscaldi, D., & Motta, E. (2021). Generating knowledge graphs by employing 
Natural Language Processing and Machine Learning techniques within the scholarly domain. Future Generation Computer Systems, 116, 253-264.
```
 
 If you use this work please cite:
 ```
 @article{dessi2021generating,
  title={Generating knowledge graphs by employing Natural Language Processing and Machine Learning techniques within the scholarly domain},
  author={Dess{\`\i}, Danilo and Osborne, Francesco and Recupero, Diego Reforgiato and Buscaldi, Davide and Motta, Enrico},
  journal={Future Generation Computer Systems},
  volume={116},
  pages={253--264},
  year={2021},
  publisher={Elsevier}
}

@inproceedings{dessi2020ai,
  title={Ai-kg: an automatically generated knowledge graph of artificial intelligence},
  author={Dess{\`\i}, Danilo and Osborne, Francesco and Reforgiato Recupero, Diego and Buscaldi, Davide and Motta, Enrico and Sack, Harald},
  booktitle={International Semantic Web Conference},
  pages={127--143},
  year={2020},
  organization={Springer}
}
 ```


![Scientific Knowledge Graph Generator Schema](https://github.com/danilo-dessi/skg/blob/master/skg_schema.png)
**Figure 1**: Scientific Knowledge Graph Generator Schema

## Repository Description

- **data-preparation/** contains the scripts used to model the data downloaded from MAG dataset about the Semantic Web into a format that can be mined by the Luan Yi et al. tool. 

- **luanyi-extractor/** contains the scripts we have changed from the original project for adapting the Luan Yi et al. tool to our data. (**ATTENTION**: they have to be copied into the Luan Yi et al. project after that it works and its models have been built.)

- **cso-openie-extractor/** contains the scripts that have been used to enrich the Luan Yi et al. result wirh CSO topics and Stanford Core NLP relations (i.e., OpenIE and verbs detected by the PoS tagger).

- **skg-generator/** contains the scripts for performing all operations to clean entities and relations and making triples. Its final step is the generation of our scientific knowledge graph triples.

- **evaluation/** contains the scripts we used to generate the sample of triples about the semantic web and evaluate our approach.

Some files have been removed form the repository for github limitations on big files. Send an email to danilo_dessi@unica.it (Danilo Dessì) to get a copy of them.


## Usage
Please follow this guide to run the code and reproduce our results. Please contact us because we need to provide extra files that cannot be pushed into the github reporsitory for files limit of 100 MB.

### Environments
Our project uses both Python 2.7 and Python 3.6 (ensure you have Python 3.6 or above installed.). Python2.7 is used to run the Luan Yi et al. tool.


### Downloads 
1. Clone the repository on your local environment
2. Download and unzip the [Stanford Core NLP]( https://stanfordnlp.github.io/CoreNLP/) modules put them under skg/stanford-corenlp-full-2018-10-05. 
3. Download and unzip the [Luan Yi et al. work](https://bitbucket.org/luanyi/scierc/src/master/) and move all files under luanyi-extractor/master/. Follow the instruction in that repository to verify that all libraries have been installed, train the model on their data, and check if the tool correctly works. As model we performed all experiments with their scientific_best_ner model. (**ATTENTION**: be sure that their scripts are properly working, we faced some issues on machines without GPUs.)


### Requirements
1. Go to the main folder skg/
2. Install Python3.7 requirements by running:
```
pip3 install -r requirements.txt
```
3. Download English package for spaCy using 
```
python3 -m spacy download "en_core_web_sm"
```

### Data preparation
1. Go to the directory data-preparation/. It contains the abstracts coming from the MAG datasets, a script to parse them and produce the input files that will be fed to the Luan Yi et al. tool.

2. To prepare the data you need to run:

```
python3 parse_input.py
```

3. The script produces:
- a directory **luanyi_input/** that contains the input files to be fed to the Luanyi tools
- **data.csv** a file that contains the mag_id, title, abstract, keywords, and doi (when available) of publications
- **all_abstracts.txt** a textual file that contains all abstracts and that will be used later by the pipeline

You can skip these steps if your data are in the format required by the Luan Yi et al. tool.


### Extraction with Luan Yi et al. tool

To extract entities and relations from scientific publications our work has been built on top of https://arxiv.org/abs/1808.09602
1. Go to the directory luanyi-extractor/
2. Please be sure you have already downloaded and tested the files coming from https://bitbucket.org/luanyi/scierc/src/master/
3. Under master/ create the directories paths data/processed_data/json/ and data/processed_data/elmo/
4. From data-preparation/ copy the directory **luanyi_input/** to master/data/processed_data/json/
5. Create an empty directory luanyi_input/ (same name of above) also under master/data/processed_data/elmo/
6. Go to master/
7. Copy the files from the directory use/ to the directory master/
8. Run 
```
python generate_elmo.py
```

9. Run
```
python3 run_luanyi.py
```

The execution will produce a csv file called *luanyi_output.csv* under the luanyi-extractor/ directory.

The execution will also produce the directory **csv_e_r/** that contains files where for each sentence a list of entities and a list of relations are associated. 

We suggest to run above commands in background since they are very time consuming.


### Extraction of CSO entities and Stanford Core NLP relations
1. Go to the cso-openie-extractor
2. Copy here the *luanyi_output.csv* previously generated in the directory luanyi-extractor/
3. Run
```
python3 run_extractors.py
```

4. The result is a csv file called *csv_e_r_full.csv* which contains all entities and relations extracted by the used tools


### Toward the SKG
This code generates heristic based relations through the window of verbs, and validates entities based on CSO topics, Semantic Web Keywords and statistics. Finally it maps all relations following the taxonomy "SKG_predicates" we defined. 

1. Go to skg-generator
2. Download and unzip the archive we provided in this directory.
3. Copy the *csv_e_r_full.csv* in this directory
4. Run
```
python3 run.py
```
5. At the end the files *selected_triples.csv* and *kg.graphml* will be generated.  The file *selected_triples.csv* contains all triples with other information generated with our method. The file *triples.csv* contains all triples generated without details. The script *to_rdf.py* can be used to generate the rdf and nt files.


### Evaluation

The directory evalution contains the scripts we used for performing our evaluation and the manually annotated gold standard.

### Other info

All the code has been developed on a server which mounts Ubuntu 17.10. Physical components were:
- 16 GB RAM memory
- 1 TB HDD
- TITAN X GPU
- Intel(R) Core(TM) i3-7100 CPU @ 3.90GHz

The execution of all modules required about 2 days.








