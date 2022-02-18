from hash import hashmulti
import param as P


def construct_streamhash_sketch(shingle_vector, H):
    projection = []

    for shingle, count in shingle_vector.items():

        hashed = [count * hashmulti(shingle, H[i]) for i in range(P.L)]

        if len(projection) == 0:
            projection = hashed
        else:
            projection = [a + b for a, b in zip(projection, hashed)]

    sketch = [1 if p >= 0 else 0 for p in projection]
    return sketch, projection


def streamhash_similarity(sketch1, sketch2):
    assert len(sketch1) == len(sketch2)
    # return sum([1 if a == b else 0 for a, b in zip(sketch1, sketch2)]) / P.L
    return sum([1 if a == b else 0 for a, b in zip(sketch1, sketch2)]) / P.L
