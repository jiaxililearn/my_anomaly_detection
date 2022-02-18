import logging
import math

from streamhash import *
import param as P

ANOMALY = -1
UNSEEN = -2


def construct_centroid_sketches(streamhash_projections, clusters, nclusters):
    """
    >>> construct_centroid_sketches({0:[-1,1,3,-3], 1:[1,1,-1,1]}, {0:[0],1:[1]}, 2)
    ({0: [0, 1, 1, 0], 1: [1, 1, 0, 1]}, {0: [-1.0, 1.0, 3.0, -3.0], 1: [1.0, 1.0, -1.0, 1.0]})
    """
    centroid_projections = {}
    centroid_sketches = {}

    for c in range(nclusters):
        for gid in clusters[c]:

            if c not in centroid_projections.keys():
                centroid_projections[c] = streamhash_projections[gid]
            else:
                centroid_projections[c] = \
                    [a + b for a, b in zip(centroid_projections[c], streamhash_projections[gid])]

    for c in range(nclusters):
        cluster_size = len(clusters[c])
        centroid_projections[c] = [p / cluster_size for p in centroid_projections[c]]
        centroid_sketches[c] = [1 if p >= 0 else 0 for p in centroid_projections[c]]

    return centroid_sketches, centroid_projections


def update_distances_and_clusters(gid,
                                  projection_delta,
                                  graph_sketches,
                                  graph_projections,
                                  centroid_sketches,
                                  centroid_projections,
                                  cluster_sizes,
                                  cluster_map,
                                  anomaly_scores,
                                  anomaly_threshold,
                                  cluster_thresholds):
    nclusters = len(cluster_sizes)
    distances = []
    min_distance = 5.0
    nearest_cluster = -1

    logging.debug(f"\t Updating edge for gid: {gid}")
    for i in range(0, nclusters):

        # logging.debug(f"graph {gid} sketch: {graph_sketches[gid]}")
        # logging.debug(f"cluster {i} sketch: {centroid_sketches[i]}")
        dist = 1.0 - math.cos(
            P.PI * (1.0 - streamhash_similarity(graph_sketches[gid],
                                                centroid_sketches[i]))
        )
        distances.append(dist)
        if dist < min_distance:
            min_distance = dist
            nearest_cluster = i
    logging.debug(f"Distances: {distances}")

    if gid not in cluster_map.keys():
        cluster_map[gid] = UNSEEN

    anomaly_scores[gid] = min_distance

    current_cluster = cluster_map[gid]
    logging.debug(f"Current Cluster: {current_cluster}")
    logging.debug(f"Nearest Cluster: {nearest_cluster}")

    if min_distance > min(anomaly_threshold, cluster_thresholds[nearest_cluster]):
        logging.debug(
            f"min distance {min_distance} > threshold {min(anomaly_threshold, cluster_thresholds[nearest_cluster])}")
        cluster_map[gid] = ANOMALY

        if current_cluster != UNSEEN and current_cluster != ANOMALY:
            old_cluster_size = cluster_sizes[current_cluster]
            cluster_sizes[current_cluster] -= 1

            # update cluster centroid projection/sketch
            centroid_p = centroid_projections[current_cluster]
            centroid_s = centroid_sketches[current_cluster]
            graph_projection = graph_projections[gid]

            for l in range(0, P.L):
                centroid_p[l] = (centroid_p[l] * old_cluster_size -
                                 (graph_projection[l] - projection_delta[l])) / (old_cluster_size - 1)
                centroid_s[l] = 1 if centroid_p[l] >= 0 else 0

            # update anomaly score if current cluster == nearest cluster (centroid moved)
            if current_cluster == nearest_cluster:
                anomaly_scores[gid] = 1.0 - math.cos(
                    P.PI * (1.0 - streamhash_similarity(graph_sketches[gid],
                                                        centroid_s)))
    else:  # else if distance <= threshold:
        # if current cluster != nearest centroid:
        logging.debug(
            f"min distance {min_distance} <= threshold {min(anomaly_threshold, cluster_thresholds[nearest_cluster])}")
        if current_cluster != nearest_cluster:
            # change cluster mapping from current to new cluster
            cluster_map[gid] = nearest_cluster
            logging.debug(f"\tNew cluster: {nearest_cluster}")

            # if a previous cluster existed
            if current_cluster != UNSEEN and current_cluster != ANOMALY:
                old_cluster_size = cluster_sizes[current_cluster]
                cluster_sizes[current_cluster] -= 1

                # update cluster centroid projection/sketch
                centroid_p = centroid_projections[current_cluster]
                centroid_s = centroid_sketches[current_cluster]
                graph_projection = graph_projections[gid]

                logging.debug(f"\tPrev. cluster centroid before removing graph: {centroid_p[:10]}")

                for l in range(0, P.L):
                    centroid_p[l] = (centroid_p[l] * old_cluster_size -
                                     (graph_projection[l] - projection_delta[l])) / (old_cluster_size - 1)
                    centroid_s[l] = 1 if centroid_p[l] >= 0 else 0

                logging.debug(f"\tPrev. cluster centroid after removing graph: {centroid_p[:10]}")

            # add to new cluster
            old_cluster_size = cluster_sizes[nearest_cluster]
            cluster_sizes[nearest_cluster] += 1

            # update new cluster centroid projection/sketch
            centroid_p = centroid_projections[nearest_cluster]
            centroid_s = centroid_sketches[nearest_cluster]
            graph_projection = graph_projections[gid]

            logging.debug(f"\tNew cluster centroid before adding graph: {centroid_p[:10]}")
            logging.debug(f"\tAdding graph: {graph_projection[:10]}")

            for l in range(0, P.L):
                centroid_p[l] = (centroid_p[l] * old_cluster_size +
                                 graph_projection[l]) / (old_cluster_size + 1)
                centroid_s[l] = 1 if centroid_p[l] >= 0 else 0

            # update anomaly score wrt. nearest cluster (centroid moved)
            anomaly_scores[gid] = 1.0 - math.cos(
                P.PI * (1.0 - streamhash_similarity(graph_sketches[gid],
                                                    centroid_s)))
            logging.debug(f"\tNew cluster centroid after adding graph: {centroid_p[:10]}")
            logging.debug(f"\tNew anomaly score: {anomaly_scores[gid]}")

        else:  # current_cluster = nearest_centroid
            # only update the current_cluster centroid using the projection delta
            current_cluster_size = cluster_sizes[current_cluster]
            centroid_p = centroid_projections[current_cluster]
            centroid_s = centroid_sketches[current_cluster]

            logging.debug(f"\tModified graph: {graph_projections[gid][:10]}")
            logging.debug(f"\tDelta: {projection_delta[:10]}")

            for l in range(0, P.L):
                centroid_p[l] += projection_delta[l] / current_cluster_size
                centroid_s[l] = 1 if centroid_p[l] >= 0 else 0

            # update anomaly score wrt. nearest cluster (centroid moved)
            anomaly_scores[gid] = 1.0 - math.cos(
                P.PI * (1.0 - streamhash_similarity(graph_sketches[gid],
                                                    centroid_s)))
            logging.debug(
                f"\tExisting cluster centroid after modifying graph: {centroid_p[:10]}")
            logging.debug(f"\tNew anomaly score: {anomaly_scores[gid]}")

        return


if __name__ == '__main__':
    import doctest
    doctest.testmod()
