import logging


def hashmulti(key, randbits):
    strip_key = key.strip()
    # logging.debug(f"hashing {strip_key} .. with {randbits[: len(strip_key)]}")
    sum = randbits[0]
    for i in range(len(strip_key.strip(' '))):
        sum += randbits[i + 1] * (ord(strip_key[i]) & 0xff)

    return 2 * int((sum >> 63) & 1) - 1
