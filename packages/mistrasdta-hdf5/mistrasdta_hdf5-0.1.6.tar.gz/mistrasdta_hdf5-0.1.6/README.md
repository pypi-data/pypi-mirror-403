# MistrasDTA-hdf5

Python tools for **streaming ingestion of Mistras DTA acoustic emission data**
with **incremental HDF5 export**, designed for use in modern Python
applications and data pipelines.

This project is a **fork of**
[MistrasDTA](https://github.com/d-cogswell/MistrasDTA) by Daniel A. Cogswell.
It preserves the original binary parsing logic while introducing a
generator-based streaming API and native HDF5 output.

---

## Background

Mistras DTA files contain binary-encoded acoustic emission (AE) hit summaries,
waveforms, and hardware metadata. The file structure is described in
*Appendix II of the Mistras User Manual*.

The original **MistrasDTA** package focuses on reading entire files into memory
and returning NumPy record arrays.  
**MistrasDTA-hdf5** is optimized instead for:

- large DTA files
- incremental / streaming processing
- integration into Python applications and services
- persistent, schema-stable HDF5 storage

---

## Key differences from upstream MistrasDTA

Compared to the original project, this fork provides:

- **Streaming parser** (`read_bin_stream`) using Python generators
- **Incremental processing** of hits, waveforms, and metadata
- **Waveforms as scaled NumPy arrays** (not raw byte blobs)
- **Native HDF5 export** with chunked, append-only datasets
- Clear separation of:
  - hit data
  - waveform data
  - waveform metadata
  - hardware and test metadata

The original `read_bin()` API is intentionally **not preserved** to avoid
implicit full-file loading and memory coupling.

---

## Installation

Install from PyPI:

```
pip install mistrasdta-hdf5[hdf5]
```
where [hdf5] is an optional dependency (required only for output to h5 files).

## Usage

- Streaming parse of a DTA file

```
from mistrasdta_hdf5 import read_bin_stream

for tag, obj in read_bin_stream("cluster.DTA"):
    if tag == "rec":
        # acoustic emission hit
        print(obj["RTOT"], obj["ENER"])
    elif tag == "wfm":
        # waveform
        print(obj["CID"], obj["WAVEFORM"].shape)
    elif tag == "meta":
        # metadata (hardware, test start time, ...)
        print(obj)
```
        
- Stream directly to HDF5

```
from mistrasdta_hdf5 import stream_to_h5

stream_to_h5(
    dta_path="cluster.DTA",
    h5_path="cluster.h5",
    skip_wfm=False,
    chunk=10000,
)
```

The resulting HDF5 file contains:

```
/hits/RTOT
/hits/CID
/hits/<parametric fields>

/waveforms
/waveforms_meta/CID
/waveforms_meta/SRATE
/waveforms_meta/TDLY

/file attributes:
  test_start_time
  hardware configuration
```

## License and attribution

This project is released under the MIT License.

Original work:

Copyright © 2019–2024
Daniel A. Cogswell

Modifications and extensions:

Copyright © 2026
Robert Farla

See LICENSE for full details.

## Disclaimer
This project is not affiliated with, endorsed by, or supported by Mistras.
It is an independent, community-driven tool provided “as is”.
