#!/bin/bash

# docker run \
#   -v /Users/jiaxili/Documents/study/code_repo/sbustreamspot-core:/app \
#   -v /Users/jiaxili/Documents/study/code_repo/sbustreamspot-data:/data \
#   -v /Users/jiaxili/Documents/study/code_repo/streamspot-bootstrap-clusters:/data/bootstrap \
#   streamspot \
#   /app/streamspot --edges=/app/test_edges.txt \
#              --bootstrap=/app/test_bootstrap_clusters.txt \
#              --chunk-length=10 \
#              --num-parallel-graphs=10 \
#              --max-num-edges=10 \
#              --dataset=all


docker run \
  -v /Users/jiaxili/Documents/study/code_repo/sbustreamspot-core:/app \
  -v /Users/jiaxili/Documents/study/code_repo/sbustreamspot-data:/data \
  -v /Users/jiaxili/Documents/study/code_repo/streamspot-bootstrap-clusters:/data/bootstrap \
  streamspot \
  /app/streamspot --edges=/data/all.tsv \
             --bootstrap=/app/test_bootstrap_clusters.txt \
             --chunk-length=10 \
             --num-parallel-graphs=10 \
             --max-num-edges=10 \
             --dataset=all
