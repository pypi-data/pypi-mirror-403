import numpy as np
import h5py

from .stream import read_bin_stream


def stream_to_h5(dta_path, h5_path, skip_wfm=False, chunk=10_000):
    """
    Stream a DTA file into an HDF5 file incrementally.
    """
    field_names = {"RTOT", "CID"}
    hits_buf = []

    with h5py.File(h5_path, "w") as h5f:
        dt_vlen = h5py.vlen_dtype(np.float64)

        wfm_ds = h5f.create_dataset(
            "waveforms", shape=(0,), maxshape=(None,), dtype=dt_vlen
        )
        wfm_meta = h5f.create_group("waveforms_meta")
        for name, dtype in [("CID", "i4"), ("SRATE", "f8"), ("TDLY", "i4")]:
            wfm_meta.create_dataset(name, shape=(0,), maxshape=(None,), dtype=dtype)

        hits_grp = h5f.create_group("hits")
        hits_grp.create_dataset("RTOT", shape=(0,), maxshape=(None,), dtype="f8")
        hits_grp.create_dataset("CID", shape=(0,), maxshape=(None,), dtype="i4")

        def ensure_fields():
            for f in field_names:
                if f in hits_grp:
                    continue
                hits_grp.create_dataset(
                    f,
                    shape=(0,),
                    maxshape=(None,),
                    dtype="f8",
                    fillvalue=np.nan,
                )

        def flush_hits():
            nonlocal hits_buf
            if not hits_buf:
                return

            ensure_fields()
            n0 = hits_grp["RTOT"].shape[0]
            n1 = n0 + len(hits_buf)

            for ds in hits_grp.values():
                ds.resize((n1,))

            for i, rec in enumerate(hits_buf):
                idx = n0 + i
                for k, ds in hits_grp.items():
                    ds[idx] = rec.get(k, np.nan)

            hits_buf = []

        for tag, obj in read_bin_stream(dta_path, skip_wfm):
            if tag == "rec":
                hits_buf.append(obj)
                field_names |= obj.keys()
                if len(hits_buf) >= chunk:
                    flush_hits()

            elif tag == "wfm" and not skip_wfm:
                i = wfm_ds.shape[0]
                wfm_ds.resize((i + 1,))
                wfm_ds[i] = obj["WAVEFORM"]

                for name in ("CID", "SRATE", "TDLY"):
                    ds = wfm_meta[name]
                    ds.resize((ds.shape[0] + 1,))

                    value = obj.get(name)
                    if value is None:
                        value = 0   # sentinel for "unknown"

                    ds[-1] = value

            elif tag == "meta":
                if "test_start_time" in obj:
                    h5f.attrs["test_start_time"] = obj[
                        "test_start_time"
                    ].isoformat()

        flush_hits()

    return h5_path
