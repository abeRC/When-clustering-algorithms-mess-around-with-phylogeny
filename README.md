# When clustering algorithms mess around with phylogeny

## Basic idea: 

* run k-means on phylogenetic trees* and see what happens;
* restricting the analysis to families of Gnathostomata (jawed vertebrates) seems like a sound choice;
* the phylogenetic tree data comes from [NCBI's Taxonomy Browser](https://www.ncbi.nlm.nih.gov/Taxonomy/);
* and individual family data comes from [Wikipedia](https://en.wikipedia.org).

## How/why this came about:

* so I could use it to illustrate text mining on a presentation about text mining (duh), which also ended up touching on unsupervised learning, phylogeny, k-means and algorithmic discrimination.

Note: code is considerably messy but I encourage the reader to dive in and do more funky data science stuff with philogenetic trees and such.

PS: saving the models is really cool to get reproducible results and I did essentially zero tinkering with the parameters, so you might want to look at those and also some metrics to guide your judgment.