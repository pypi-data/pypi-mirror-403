import logging
import struct
from datetime import datetime

import numpy as np

from .constants import CHID_to_str, CHID_byte_len, bytes_to_rtot


def read_bin_stream(file, skip_wfm: bool = False):
    """
    Streaming parser for Mistras DTA files.

    Yields:
      ("rec", record_dict)   AE hit records
      ("wfm", wfm_dict)      AE waveform records
      ("meta", meta_dict)    metadata (hardware, test start time)
    """
    CHID_list = []
    hardware = []
    gain = {}
    test_start_time = None

    with open(file, "rb") as data:
        byte = data.read(2)

        while byte != b"":
            (LEN,) = struct.unpack("H", byte)
            (b1,) = struct.unpack("B", data.read(1))
            LEN -= 1

            # IDs 40–49 have an extra byte
            if 40 <= b1 <= 49:
                data.read(1)
                LEN -= 1

            # --------------------------------------------------
            # 1 – Hit / Event
            # --------------------------------------------------
            if b1 == 1:
                RTOT = bytes_to_rtot(data.read(6))
                LEN -= 6

                (CID,) = struct.unpack("B", data.read(1))
                LEN -= 1

                record = {"RTOT": RTOT, "CID": CID}

                for CHID in CHID_list:
                    b = CHID_byte_len.get(CHID, 0)
                    name = CHID_to_str.get(CHID, str(CHID))

                    if b == 0:
                        continue

                    if name == "RMS":
                        (v,) = struct.unpack("H", data.read(b))
                        v /= 5000.0
                    elif name == "DURATION":
                        (v,) = struct.unpack("i", data.read(b))
                    elif name == "SIG STRENGTH":
                        (v,) = struct.unpack("i", data.read(b))
                        v *= 3.05
                    elif name == "ABS-ENERGY":
                        (v,) = struct.unpack("f", data.read(b))
                        v *= 9.31e-4
                    elif b == 1:
                        (v,) = struct.unpack("B", data.read(b))
                    elif b == 2:
                        (v,) = struct.unpack("H", data.read(b))
                    else:
                        v = data.read(b)

                    LEN -= b
                    record[name] = v

                if LEN > 0:
                    data.read(LEN)

                yield ("rec", record)

            # --------------------------------------------------
            # 7 – User comment
            # --------------------------------------------------
            elif b1 == 7:
                if LEN > 0:
                    try:
                        msg = data.read(LEN)
                        logging.info(msg.decode("ascii").strip("\x00"))
                    except Exception:
                        pass

            # --------------------------------------------------
            # 8 – Continued file
            # --------------------------------------------------
            elif b1 == 8:
                if LEN >= 8:
                    data.read(8)
                    LEN -= 8
                if LEN > 0:
                    data.read(LEN)

            # --------------------------------------------------
            # 41 – ASCII Product Definition
            # --------------------------------------------------
            elif b1 == 41:
                if LEN >= 2:
                    data.read(2)
                    LEN -= 2
                if LEN > 0:
                    try:
                        logging.info(data.read(LEN)[:-3].decode("ascii"))
                    except Exception:
                        pass

            # --------------------------------------------------
            # 42 – Hardware Setup
            # --------------------------------------------------
            elif b1 == 42:
                if LEN >= 2:
                    data.read(2)
                    LEN -= 2

                while LEN > 0:
                    (LSUB,) = struct.unpack("H", data.read(2))
                    LEN -= 2

                    SUBID = struct.unpack("B", data.read(1))[0]
                    LSUB -= 1
                    LEN -= 1

                    if SUBID == 5:
                        (nCHID,) = struct.unpack("B", data.read(1))
                        CHID_list = list(
                            struct.unpack(f"{nCHID}B", data.read(nCHID))
                        )
                        LSUB -= 1 + nCHID
                        LEN -= 1 + nCHID

                    elif SUBID == 23:
                        CID, V = struct.unpack("BB", data.read(2))
                        gain[CID] = V
                        LSUB -= 2
                        LEN -= 2

                    elif SUBID == 173:
                        SUBID2 = struct.unpack("B", data.read(1))[0]
                        LSUB -= 1
                        LEN -= 1

                        if SUBID2 == 42:
                            data.read(2)   # MVERN
                            data.read(1)   # ADT
                            data.read(2)   # SETS
                            data.read(2)   # SLEN
                            CHID_val = struct.unpack("B", data.read(1))[0]
                            data.read(2)   # HLK
                            data.read(2)   # HITS
                            SRATE = struct.unpack("H", data.read(2))[0]
                            data.read(2)   # TMODE
                            data.read(2)   # TSRC
                            TDLY = struct.unpack("h", data.read(2))[0]
                            data.read(2)   # MXIN
                            data.read(2)   # THRD

                            hardware.append((CHID_val, 1000 * SRATE, TDLY))

                            consumed = 2 + 1 + 2 + 2 + 1 + 2 + 2 + 2 + 2 + 2 + 2 + 2
                            LSUB -= consumed
                            LEN -= consumed

                    if LSUB > 0:
                        data.read(LSUB)
                        LEN -= LSUB

                if hardware:
                    hw_arr = np.core.records.fromrecords(
                        hardware, names=["CH", "SRATE", "TDLY"]
                    )
                    yield ("meta", {"hardware": hw_arr})

            # --------------------------------------------------
            # 99 – Test start time
            # --------------------------------------------------
            elif b1 == 99:
                text = data.read(LEN).decode("ascii").strip("\x00")
                test_start_time = datetime.strptime(
                    text, "%a %b %d %H:%M:%S %Y\n"
                )
                yield ("meta", {"test_start_time": test_start_time})

            # --------------------------------------------------
            # 128–130 – Resume / Stop / Pause
            # --------------------------------------------------
            elif b1 in (128, 129, 130):
                if LEN >= 6:
                    data.read(6)
                    LEN -= 6
                if LEN > 0:
                    data.read(LEN)

            # --------------------------------------------------
            # 173 – Waveform
            # --------------------------------------------------
            elif b1 == 173:
                data.read(1)  # SUBID
                TOT = bytes_to_rtot(data.read(6))
                CID = struct.unpack("B", data.read(1))[0]
                data.read(1)  # ALB
                LEN -= 9

                MaxInput = 10.0
                Gain = 10 ** (gain.get(CID, 0) / 20.0)
                AmpScaleFactor = MaxInput / (Gain * 32768.0)

                if LEN > 0:
                    samples = struct.unpack(f"{LEN//2}h", data.read(LEN))
                    V = AmpScaleFactor * np.asarray(samples, dtype=np.float64)

                    if not skip_wfm:
                        SRATE = TDLY = None
                        if hardware:
                            hw = np.asarray(hardware)
                            match = hw[hw[:, 0] == CID]
                            if len(match):
                                SRATE, TDLY = match[0, 1], match[0, 2]

                        yield (
                            "wfm",
                            {
                                "TOT": TOT,
                                "CID": CID,
                                "SRATE": SRATE,
                                "TDLY": TDLY,
                                "WAVEFORM": V,
                            },
                        )

            else:
                if LEN > 0:
                    data.read(LEN)

            byte = data.read(2)
