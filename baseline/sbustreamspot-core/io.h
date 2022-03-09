/*
 * Copyright 2016 Emaad Ahmed Manzoor
 * License: Apache License, Version 2.0
 * http://www3.cs.stonybrook.edu/~emanzoor/streamspot/
 */

#ifndef STREAMSPOT_IO_H_
#define STREAMSPOT_IO_H_

#include "graph.h"
#include <string>
#include <tuple>
#include <vector>

namespace std {

tuple<uint32_t,vector<edge>,unordered_map<uint32_t,vector<edge>>,uint32_t>
  read_edges(string filename, const unordered_set<uint32_t>& train_gids,
             const unordered_set<uint32_t>& scenarios);
tuple<vector<vector<uint32_t>>, vector<double>, double>
  read_bootstrap_clusters(string bootstrap_file);

void write_sketches_to_file(string filename, vector<bitset<L>> sketches);
void write_anomaly_scores_to_file(string filename, vector<double> scores);
void write_anomaly_iterations_to_file(string filename, vector<vector<double>> iterations);
void write_cluster_iterations_to_file(string filename, vector<vector<int>> iterations);
}

#endif
