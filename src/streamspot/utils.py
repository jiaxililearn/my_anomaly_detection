import random
import param as P


def split_list_to_chunks(lst, n):
    """
    >>> split_list_to_chunks([1,2,3,4,5], 2)
    [[1, 2], [3, 4], [5]]
    """
    return [lst[i:i + n] for i in range(0, len(lst), n)]


def allocate_random_bits(chunk_length):
    H = []
    for i in range(P.L):
        H.append([random.getrandbits(64) for _ in range(chunk_length + 2)])
    return H


def find_common_short_shigle(new_shingle, src_type, outgoing_edges):
    for dst_id, dst_type, e_type in outgoing_edges:
        exist_shingle = f"{src_type}{e_type}{dst_type}"
        if new_shingle.startswith(exist_shingle):
            return exist_shingle


if __name__ == '__main__':
    import doctest
    doctest.testmod()
