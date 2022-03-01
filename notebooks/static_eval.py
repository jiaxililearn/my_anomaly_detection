#!/usr/bin/env python
# coding: utf-8

# ## Create Training from Bootstrap

# In[1]:


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


# In[2]:


edges = '../baseline/sbustreamspot-data/all.tsv'
bootstrap = '../baseline/streamspot-bootstrap-clusters/01-C50_k10_all.txt'
chunk_length = 50
num_parallel_graphs = 10
max_num_edges = 100


# In[3]:


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


# In[21]:


H = U.allocate_random_bits(chunk_length)


# ### Get test sketches

# In[ ]:


test_graph = {}

for gid, edges in test_edges.items():
#     print(e[:10])
    logging.debug(f'updating test graph {gid}')
    for e in edges:
        update_graphs(e, test_graph)
test_graph


# In[ ]:



#Construct static test Shingles
test_streamhash_sketches = {}
test_streamhash_projections = {}
for gid in test_gids:
    logging.info(f" {gid}")
    temp_shingle_vector = construct_temp_shingle_vector(test_graph[gid],
                                                        chunk_length)
    
    test_streamhash_sketches[gid], test_streamhash_projections[gid]         = construct_streamhash_sketch(temp_shingle_vector, H)
    
    logging.debug(f"Sketch for test graph {gid}: {test_streamhash_sketches[gid]}")
#     logging.debug(f"Projection for test graph {gid}: {test_streamhash_projections[gid]}")

with open('test_graph_sketches.json', 'w') as fout:
    fout.write(json.dumps(test_streamhash_sketches))
with open('test_graph_projections.json', 'w') as fout:
    fout.write(json.dumps(test_streamhash_projections))


# In[ ]:




