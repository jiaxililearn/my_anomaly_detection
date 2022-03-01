#!/usr/bin/env python
# coding: utf-8

# ## Create Training from Bootstrap

# In[18]:


import logging
import random
import click
import math
from collections import deque
from copy import copy
import time
import json
import sys
sys.path.insert(0, '../src/streamspot')

from iostream import *
from graph import *
from streamhash import *
from cluster import *
import utils as U
import param as P

logging.basicConfig(level=logging.DEBUG)


# In[19]:


edges = '../baseline/sbustreamspot-data/all.tsv'
bootstrap = '../baseline/streamspot-bootstrap-clusters/01-C50_k10_all.txt'
chunk_length = 50
num_parallel_graphs = 10
max_num_edges = 100


# In[ ]:


par = int(num_parallel_graphs)

clusters, cluster_thresholds, global_threshold = read_bootstrap_clusters(bootstrap)
cluster_sizes = []
train_gids = set()
cluster_map = {}

statistics = []

for i, cluster in clusters.items():
    cluster_sizes.append(len(cluster))
    for g in cluster:
        train_gids.add(g)
        cluster_map[g] = i

logging.debug(f"Training Graphs: {train_gids}")

test_gids, train_edges, test_edges, num_test_edges = read_edges(edges, train_gids)
random.shuffle(test_gids)

# make groups of size par(parallel flowing graphs)
groups = U.split_list_to_chunks(test_gids, par)
logging.debug(f"Split in {par} groups: {groups}")

logging.info(f"Constructing {len(train_gids)} training graphs:")

graphs = {}
for e in train_edges:
    update_graphs(e, graphs)

H = U.allocate_random_bits(chunk_length)

logging.info("Constructing StreamHash sketches for training graphs:")
streamhash_sketches = {}
streamhash_projections = {}
for gid in train_gids:
    logging.info(f" {gid}")
    temp_shingle_vector = construct_temp_shingle_vector(graphs[gid],
                                                        chunk_length)
    streamhash_sketches[gid], streamhash_projections[gid]         = construct_streamhash_sketch(temp_shingle_vector, H)
    logging.debug(f"Sketch for graph {gid}: {streamhash_sketches[gid]}")
    logging.debug(f"Projection for graph {gid}: {streamhash_projections[gid]}")

for gid1 in train_gids:
    for gid2 in train_gids:
        sim = math.cos(
            P.PI * (1.0 - streamhash_similarity(streamhash_sketches[gid1],
                                                streamhash_sketches[gid2]))
        )
        logging.debug(f"graph {gid1} and {gid2} similarity: {sim}")

logging.info("Constructing bootstrap cluster centroids:")
centroid_sketches, centroid_projections =     construct_centroid_sketches(streamhash_projections, clusters, len(clusters.keys()))

anomaly_scores = {}
for gid in train_gids:
    anomaly_scores[gid] = 1.0 - math.cos(
        P.PI * (1.0 - streamhash_similarity(streamhash_sketches[gid],
                                            centroid_sketches[cluster_map[gid]]))
    )

for gid, s in anomaly_scores.items():
    logging.debug(f"Anomaly Score - graph {gid}: {s}")
for gid, c in cluster_map.items():
    logging.debug(f"Cluster - graph {gid}: {c}")

logging.info('saving centroid sketches ..')
with open('centroid_sketches.json','w') as fout:
    fout.write(json.dumps(centroid_sketches))
logging.info('saving centroid projections ..')
with open('centroid_projections.json','w') as fout:
    fout.write(json.dumps(centroid_projections))
with open('training_anomaly_scores.json','w') as fout:
    fout.write(json.dumps(anomaly_scores))


# In[ ]:




