import logging
from collections import defaultdict
from queue import Queue
import time
import math


from hash import hashmulti
import param as P
import utils as U


def remove_from_graph(e, graphs):
    src_id, src_type, dst_id, dst_type, e_type, gid = e
    logging.debug(f"Removing edge: {e}")
    g = graphs[gid]
    node = (src_id, src_type)
    dest = (dst_id, dst_type, e_type)
    edge_list = g[node]

    logging.debug(f"Edges from sources: {[x[0] for x in edge_list]}")
    if len(edge_list) == 1:
        g.pop(node)
    else:
        if len(edge_list) > 0:
            logging.debug(f"Removing dest: {dest} from {edge_list}")
            try:
                edge_list.remove(dest)
            except Exception as e:
                logging.debug(e)
                pass


def update_streamhash_sketches(e, graphs, streamhash_sketches, streamhash_projections,
                               chunk_length, H):
    src_id, src_type, dst_id, dst_type, e_type, gid = e

    if gid not in streamhash_sketches.keys():
        streamhash_sketches[gid] = [0] * P.L
        streamhash_projections[gid] = [0] * P.L

    sketch = streamhash_sketches[gid]
    projection = streamhash_projections[gid]

    g = graphs[gid]

    start = time.time()
    outgoing_edges = g[(src_id, src_type)]
    n_outgoing_edges = len(outgoing_edges)
    shingle_length = 2 * (n_outgoing_edges + 1)
    last_chunk_length = int(shingle_length - chunk_length * (shingle_length / chunk_length))

    if last_chunk_length == 0:
        last_chunk_length = chunk_length

    last_chunk = ""
    length = last_chunk_length
    i = n_outgoing_edges - 1

    while length > 0 and i >= 0:
        logging.debug('ENTER')
        logging.debug(f'i is: {i}, length is: {length}')

        logging.debug(f'last_chunk loop on dst type from edge: {outgoing_edges[i]}')
        last_chunk = outgoing_edges[i][1] + last_chunk
        length -= len(outgoing_edges[i][1])

        if length <= 0:
            break

        logging.debug(f'last_chunk loop on edge type from edge: {outgoing_edges[i]}')
        last_chunk = outgoing_edges[i][2] + last_chunk
        length -= len(outgoing_edges[i][2])

        i -= 1
    if i < 0:
        if length > 1:
            last_chunk = src_type + last_chunk
            length -= len(src_type)

        if length == 1:
            last_chunk = " " + last_chunk
            length -= 1

    sec_last_chunk = ""
    if i >= 0:
        length = chunk_length

        if last_chunk_length % 2 != 0:
            sec_last_chunk = outgoing_edges[i][2] + sec_last_chunk
            length -= len(outgoing_edges[i][2])
            i -= 1
        if i >= 0 and length >= 0:
            while length > 0 and i >= 0:
                sec_last_chunk = outgoing_edges[i][1] + sec_last_chunk
                length -= len(outgoing_edges[i][1])
                if length <= 0:
                    break

                sec_last_chunk = outgoing_edges[i][2] + sec_last_chunk
                length -= len(outgoing_edges[i][2])
                i -= 1
        if i < 0:
            if length > 1 and length <= 3:
                sec_last_chunk = src_type + sec_last_chunk
            if length == 1:
                sec_last_chunk = " " + sec_last_chunk

    # if DEBUG check last chunk if correct
    if logging.getLogger().level == 10:
        shingle = ''
        shingle += src_type

        for out_e in outgoing_edges:
            shingle += out_e[2]
            shingle += out_e[1]
        logging.debug(f"Shingle: {shingle}")
        chunks = get_string_chunk(shingle, chunk_length)
        logging.debug(f"Last chunk: {last_chunk}")
        # logging.debug(f" chunk: {chunks[-1]}")
        assert last_chunk == chunks[-1]

        if len(chunks) > 1:
            logging.debug(f"Second last chunk: {sec_last_chunk}")
            assert sec_last_chunk == chunks[-2]

    incoming_chunks, outgoing_chunks = [], []
    incoming_chunks.append(last_chunk)
    if n_outgoing_edges > 1:
        if last_chunk_length <= 1:
            outgoing_chunks.append(sec_last_chunk)
        elif last_chunk_length == 2:
            pass
        else:
            # TODO: original code was outgoing_chunks.push_back(last_chunk.substr(0, last_chunk_length - 2));
            out_edge_ = U.find_common_short_shigle(last_chunk, src_type, outgoing_edges)
            outgoing_chunks.append(out_edge_)
    end = time.time()
    shingle_construction_time = end - start

    logging.debug(f"Incoming chunks: {incoming_chunks}")
    logging.debug(f"Outgoing chunks: {outgoing_chunks}")

    projection_delta = [0] * P.L
    start = time.time()

    for chunk in incoming_chunks:
        for i in range(0, P.L):
            delta = hashmulti(chunk, H[i])
            projection[i] += delta
            projection_delta[i] += delta

    for chunk in outgoing_chunks:
        for i in range(0, P.L):
            delta = hashmulti(chunk, H[i])
            projection[i] -= delta
            projection_delta[i] -= delta

    # update sketch = sign(projection)
    for i in range(0, P.L):
        sketch[i] = 1 if projection[i] >= 0 else 0

    end = time.time()
    sketch_update_time = end - start

    return projection_delta, shingle_construction_time, sketch_update_time


def update_graphs(edge, graphs):
    """
    >>> update_graphs((71, '5', 394, '13b', '9c', 71), {71: {(71, '5'): {(394, '13b', '9c')}}})
    {71: {(71, '5'): {(394, '13b', '9c')}}}
    """
    src_id, src_type, dst_id, dst_type, e_type, gid = edge

    if gid not in graphs.keys():
        graphs[gid] = defaultdict(list)

    if (dst_id, dst_type, e_type) not in graphs[gid][(src_id, src_type)]:
        graphs[gid][(src_id, src_type)].append((dst_id, dst_type, e_type))
    return graphs


def construct_temp_shingle_vector(g, chunk_length):
    temp_shingle_vector = defaultdict(int)

    for k, v in g.items():
        logging.debug(f"OkBFT from {k[0]} {k[1]} (K = {P.K}) fanout = {len(v)}")

        shingle = ""
        q = Queue()
        d = {}

        # logging.debug(f"+put to q: {(k[0], k[1], ' ')}")
        q.put((k[0], k[1], " "))  # src_id, src_type, " "
        d[k[0]] = 0

        while not q.empty():
            uid, utype, etype = q.get()
            # logging.debug(f"-pop from q: {(uid, utype, etype)}")

            shingle += etype
            shingle += utype

            # logging.debug(f"single: {shingle}")

            if d[uid] == P.K:
                continue

            # logging.debug(f"getting outgoing edges from: {uid} {utype}")
            for e in g[(uid, utype)]:
                vid = e[0]
                d[vid] = d[uid] + 1

                # logging.debug(f"+o push to q: {e}")
                q.put(e)
        for chunk in get_string_chunk(shingle, chunk_length):
            temp_shingle_vector[chunk] += 1

    logging.debug("Shingle in Graph: ")
    for k, v in temp_shingle_vector.items():
        logging.debug(f" {k} => {v}")
    return temp_shingle_vector


def get_string_chunk(shingle, chunk_length):
    """
    >>> get_string_chunk('abcdefghijklmn', 5)
    ['abcde', 'fghij', 'klmn']
    """
    chunks = []
    for offset in range(0, len(shingle), chunk_length):
        chunks.append(shingle[offset:offset + chunk_length])

    # logging.debug(f"chunks are: {chunks}")
    return chunks


if __name__ == '__main__':
    import doctest
    doctest.testmod()
