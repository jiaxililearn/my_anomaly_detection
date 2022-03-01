import logging
from collections import defaultdict


def read_bootstrap_clusters(bootstrap_file):
    """
    >>> read_bootstrap_clusters("../../data/custom_bootstrap.txt")
    ({0: [71, 72], 1: [47, 46]}, [0.5, 0.5], 0.6)
    """
    cluster_thresholds = []
    clusters = {}

    with open(bootstrap_file, 'r') as fin:
        lines = fin.readlines()

    for i, l in enumerate(lines):
        data = l.strip('\n').split('\t')
        if i == 0:
            nclusters = int(data[0])
            global_threshold = float(data[1])
        else:
            cluster_threshold = float(data[0])
            cluster_thresholds.append(cluster_threshold)
            clusters[i - 1] = [int(c) for c in data[1:]]

    return clusters, cluster_thresholds, global_threshold


def read_edges(filename, train_gids):
    """
    >>> read_edges("../../data/test_edges.txt", {72, 47, 46, 71})
    ({48, 460}, [(71, '5', 394, '13b', '9c', 71), (72, '5', 399, '13b', '9c', 72), (47, '5', 430, '11c', '17', 47), (46, '5', 444, '128', 'b2', 46)], defaultdict(<class 'list'>, {48: [(48, '5', 430, '11c', '6a', 48)], 460: [(460, '1', 362, '13d', '4', 460)]}), 2)
    """
    logging.info(f"Reading edges from: {filename}")

    train_edges = []
    test_edges = defaultdict(list)

    # unique_graphs = set()
    num_test_edges = 0
    # num_dropped_edges = 0
    num_train_edges = 0
    test_gids = set()

    with open(filename) as fin:
        readline = fin.readline()
        while readline:
            line = readline.strip().split('\t')
            src_id = int(line[0])
            src_type = str(line[1])
            dst_id = int(line[2])
            dst_type = str(line[3])
            e_type = str(line[4])
            graph_id = int(line[5])

            if graph_id in train_gids:
                train_edges.append(
                    (src_id, src_type, dst_id, dst_type, e_type, graph_id)
                )
                num_train_edges += 1
            else:
                test_gids.add(graph_id)
                test_edges[graph_id].append(
                    (src_id, src_type, dst_id, dst_type, e_type, graph_id)
                )
                num_test_edges += 1

            readline = fin.readline()
    logging.debug(f"Train edges: {num_train_edges}")
    logging.debug(f"Test edges: {num_test_edges}")
    return list(test_gids), train_edges, test_edges, num_test_edges


if __name__ == '__main__':
    import doctest
    doctest.testmod()
