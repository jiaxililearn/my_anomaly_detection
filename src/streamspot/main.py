import logging
import random
import click
import math
from collections import deque
from copy import copy
import time
import json

from iostream import *
from graph import *
from streamhash import *
from cluster import *
import utils as U
import param as P

logging.basicConfig(level=logging.DEBUG)
# edges = "../../data/sample_edges.tsv"
# bootstrap = "../../data/custom_bootstrap.txt"
#
# chunk_length = 500
# num_parallel_graphs = 10
# max_num_edges = 100


@click.command()
@click.option('--edges', type=str, required=True, help='edge file')
@click.option('--bootstrap', type=str, required=True, help='bootstrap file')
@click.option('--chunk-length', type=int, required=True, help='chunk length')
@click.option('--num-parallel-graphs', type=int, required=True, help='num parallel graphs')
@click.option('--max-num-edges', type=int, required=True, help='max num edges')
def main(edges, bootstrap, chunk_length, num_parallel_graphs, max_num_edges):
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
        streamhash_sketches[gid], streamhash_projections[gid] \
            = construct_streamhash_sketch(temp_shingle_vector, H)
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
    centroid_sketches, centroid_projections = \
        construct_centroid_sketches(streamhash_projections, clusters, len(clusters.keys()))

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

    logging.info(f'Streaming in {num_test_edges} test edges:')

    num_intervals = math.ceil(num_test_edges / P.CLUSTER_UPDATE_INTERVAL)

    if num_intervals == 0:
        num_intervals = 1

    anomaly_score_iterations, cluster_map_iterations = {}, {}
    edge_num = 0

    cache_size = num_test_edges
    if max_num_edges > 0:
        cache_size = max_num_edges
    cache = deque()

    for group in groups:
        logging.info('Straming group: ')
        logging.debug(f"{group}")

        edge_offset = {g: 0 for g in group}

        group_copy = copy(group)

        while len(group_copy) > 0:
            gidx = random.choice(range(0, len(group_copy)))
            gid = group_copy[gidx]
            off = edge_offset[gid]

            logging.debug(f"Streaming graph {gid} offset {off}")
            e = test_edges[gid][off]

            # Process Edge

            # Check if cache is full
            if len(cache) == cache_size:
                edge_to_evict = cache.popleft()  # oldest edge
                remove_from_graph(edge_to_evict, graphs)
            cache.append(e)

            # update graph
            start = time.time()
            update_graphs(e, graphs)
            end = time.time()
            graph_update_times = end - start

            # update sketches
            projection_delta, shingle_construction_time, sketch_update_time = \
                update_streamhash_sketches(e, graphs, streamhash_sketches,
                                           streamhash_projections, chunk_length, H)
            start = time.time()
            update_distances_and_clusters(gid, projection_delta,
                                          streamhash_sketches,
                                          streamhash_projections,
                                          centroid_sketches, centroid_projections,
                                          cluster_sizes, cluster_map,
                                          anomaly_scores, global_threshold,
                                          cluster_thresholds)

            statistics.append([gid, anomaly_scores[gid], cluster_map[gid], e])

            end = time.time()
            cluster_update_times = end - start

            # store current anomaly scores and cluster assignments
            if (edge_num % P.CLUSTER_UPDATE_INTERVAL == 0) \
                    or (edge_num == num_test_edges - 1):
                anomaly_score_iterations[int(edge_num / P.CLUSTER_UPDATE_INTERVAL)] = anomaly_scores
                cluster_map_iterations[int(edge_num / P.CLUSTER_UPDATE_INTERVAL)] = cluster_map

            edge_num += 1

            last_graph_update_time = graph_update_times
            last_sketch_update_time = sketch_update_time
            last_cluster_update_time = cluster_update_times
            logging.debug(
                f"\tMost recent run times: {last_graph_update_time}us (graph), {last_sketch_update_time}us (sketch), {last_cluster_update_time}us (cluster)")

            edge_offset[gid] += 1

            if edge_offset[gid] == len(test_edges[gid]):
                group_copy.remove(gid)

                logging.debug(f"Erasing graph {group[gidx]}")
                logging.debug(f"New group: {group_copy}")

    # skip Runtimes Summary from original code

    # print size of each test graph in memory
    logging.debug("Test graph sizes: ")
    for gid in test_gids:
        size = 0
        for k, v in graphs[gid]:
            size += len(v)
        logging.debug(f"\t graph:{gid}, {size} edges ")

    logging.debug(f"Iterations {num_intervals}")
    for i in range(0, num_intervals):
        a = anomaly_score_iterations[i]
        c = cluster_map_iterations[i]
        logging.debug(a)
        logging.debug(c)

    logging.debug(f"Graph projection\n\t: {streamhash_projections}")
    logging.debug(f"Centroid projection\n\t: {centroid_projections}")

    # write output anomaly summary
    output_summary_file = '../../data/anomaly_summary.json'
    logging.info(f"wrting anomaly statistics into {output_summary_file}")
    with open(output_summary_file, 'w') as fout:
        fout.write(json.dumps(statistics))
    return


if __name__ == '__main__':
    main()

# python main.py --edges ../../baseline/sbustreamspot-core/test_edges.txt \
# --bootstrap ../../baseline/sbustreamspot-core/test_bootstrap_clusters.txt \
# --chunk-length 500 \
# --num-parallel-graphs 10 \
# --max-num-edges 100
