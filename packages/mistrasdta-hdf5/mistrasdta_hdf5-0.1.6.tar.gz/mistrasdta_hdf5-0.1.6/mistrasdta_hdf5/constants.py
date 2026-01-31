import struct

CHID_to_str = {
    1: "RISE",
    2: "PCNTS",
    3: "COUN",
    4: "ENER",
    5: "DURATION",
    6: "AMP",
    8: "ASL",
    10: "THR",
    13: "A-FRQ",
    17: "RMS",
    18: "R-FRQ",
    19: "I-FRQ",
    20: "SIG STRENGTH",
    21: "ABS-ENERGY",
    23: "FRQ-C",
    24: "P-FRQ",
}

CHID_byte_len = {
    1: 2,
    2: 2,
    3: 2,
    4: 2,
    5: 4,
    6: 1,
    8: 1,
    10: 1,
    13: 2,
    17: 2,
    18: 2,
    19: 2,
    20: 4,
    21: 4,
    23: 2,
    24: 2,
}


def bytes_to_rtot(bytes6: bytes) -> float:
    """Convert a 6-byte RTOT timestamp to seconds."""
    i1, i2 = struct.unpack("IH", bytes6)
    return (i1 + 2**32 * i2) * 0.25e-6
