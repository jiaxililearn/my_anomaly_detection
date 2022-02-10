# StreamSpot Bootstrap Clusters

[www3.cs.stonybrook.edu/~emanzoor/streamspot/](www3.cs.stonybrook.edu/~emanzoor/streamspot/)

Below are the bootstrap clusters used for the experiments in the StreamSpot paper for each of following datasets:

   * `all` (`01-C50_k10_all.txt`): Chunk length of 50, 10 clusters.
   * `ydc` (`02-C25_k5_ydc.txt`): Chunk length of 25, 5 clusters.
   * `gfc` (`03-C50_k5_gfc.txt`): Chunk length of 50, 5 clusters.

The bootstrap clusters were generated as follows:

   1. Sample 75% of the respective dataset.
   2. Select a chunk length as specified in the paper.
   3. Select the number of clusters `K` by running 10 trials of `K`-medoids and picking `K` with the maximum silhoutte coefficient on the resulting clustering.
   4. Set the anomaly threshold for each cluster as 3 standard deviations away from the mean graph-to-medoid distance of that cluster.
   5. Set the global threshold as 3 standard deviations away from the mean graph-to-medoid distance of all clusters.

The format of each bootstrap clusters file is as follows (all numbers are `TAB` separated):

```
number_of_clusters global_threshold
cluster_threshold_1 cluster_1_graph_id_1 cluster_1_graph_id_2 ...
cluster_threshold_2 cluster_2_graph_id_1 cluster_2_graph_id_2 ...
...
```

For any questions, please contact:

   * emanzoor@cs.stonybrook.edu
   * leman@cs.stonybrook.edu