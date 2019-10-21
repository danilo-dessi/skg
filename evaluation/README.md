# Evaluation
The directory evalution contains the scripts we used for performing our evaluation:

* **gs_sw_triples_01_10_definitive.xlsx+** is the file that we used to compute the majority vote labels of our gold standard
* **select_triples_to_annotate.py** chooses the triples we emplyed for our annotation. The set is saved in the file **gs_sw_triples_to_annotate.csv**
* **evaluator.py** is the script that computes precisiom, recall, and fmeasure on annotated data using the column *majority vote* within the file **gs_sw_triples_01_10_definitive.xlsx+** 