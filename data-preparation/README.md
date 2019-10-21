# Data Preparation

This directory contains the abstract coming from the MAG datasets and a script to parse them and produce the input files that will be fed to the Luan YI et al.'s tools.

To prepare the data you have to run:

```
python3 parse_input.py
```

The script produces:
- a directory **mag_sw28_full_input_luanyi** that contains the input files to be fed to the Luanyi tools
- **mag_sw28_full.csv** a file that contains the mag_id, title, abstract, keywords, and doi (when available) of publications
- **semantic_web_28k_abstracts.txt** a textual file that contains all abstracts and that will be used later by the pipeline


Please note that the script *parse_input.py* has a parameter *n_splits = 20* which splits original data in 20 subsets. This is necessary because we had problems on big set of data with the Luan Yi et al.'s tools.


