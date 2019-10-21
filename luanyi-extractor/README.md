# Luan Yi Extractor

To extract entities and relations from scientific publications our work has been built on top of https://arxiv.org/abs/1808.09602

1. To use Luan Yi et al. tool you first have to download the repository https://bitbucket.org/luanyi/scierc/src/master/. Follow the instruction in that repository to verify that all libraries have been installed and the tool is correctly working. We used their scientific_best_ner model.
2. Under master/ create the directories paths data/processed_data/json/ and data/processed_data/elmo/
2. Copy the directory **mag_sw28_full_input_luanyi** from ../data-preparation/ to master/data/processed_data/json/
4. Create an empty directory **mag_sw28_full_input_luanyi** (same name of above) also under data/processed_data/elmo/
3. Copy and Substitute the files under the directory use/ into the directory master/
4. Run 
```
python generate_elmo.py
```

5. Run
```
python3 run_luanyi.py
```

Please note that our project has been developed in Python 3.6 while the Luan Yi et al. tool uses Python 2.7.

The execution will produce the directory **csv_e_r** that contains files where for each sentence a list of entities and a list of relations are associated.  We suggest to run all the above commands in background since they are very time consuming.


