### Toward the SKG
This directory contains the source code that performs all operations to produce the scientific knowledge graph.
At the end the files *selected_triples.csv* and *kg.graphml* will be generated.  The file *selected_triples.csv* contains all triples generated with our method. The file *kg.graphml* is a file that can be read by common graph visualizer like [cytoscape](https://cytoscape.org).

The directory **classes** contains the develoepd python classes. There is almost an overlap between these classes and some modules of the pipeline. More precisely:
* **BestLabelFinder.py** &rarr; Best Label Finder
* **EntityCleaner.py** &rarr; EntitiesRefiner (in combination with StatisticsRefiner.py)
* **Mapper.py** &rarr; Mapper
* **CSORelationshipsBuilder.py** &rarr; CSO Relationships Integrator
* **Selector.py** &rarr; Relationships Selector
* **StatisticsRefiner.py** &rarr; EntitiesRefiner (in combination with EntityCleaner.py)



The file *selected_triples.csv* contains the following columns:

* **s** &rarr; the subject of the relationship
* **p** &rarr; the predicate of the relationships
* **o** &rarr; the object of the relationships
* **source** &rarr; the source method that has detected that relationship (possible values are: luanyi, openie, heuristic)
* **support** &rarr; the support of relationships
* **abstracts** &rarr; a list of abstracts where the relationship has been inferred