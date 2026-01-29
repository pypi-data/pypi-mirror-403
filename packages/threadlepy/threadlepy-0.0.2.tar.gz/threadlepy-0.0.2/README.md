# threadlepy

`threadlepy` is a minimal Python client for the **Threadle CLI** (JSON mode).  
It starts a Threadle subprocess, communicates via stdin/stdout, and exposes a thin set of command wrappers.

> **Status:** Experimental / early-stage. API may change.

---

## Installation

From PyPI (once published):

```bash
pip install threadlepy
```
Local editable install:

```bash
pip install -e .
```

Requirements
- Python 3.9+
- A working Threadle CLI executable (threadle)

Quickstart

```python
import threadlepy
import threadlepy.client as client
import threadlepy.commands as th

client.start(path="/Users/doge/Documents/Threadle/Threadle.CLIconsole/bin/Debug/net8.0/threadle")

th.set_workdir(dir="/Users/doge/Documents/Examples")

lazega_nodeset = th.load_file(
    "lazega_nodeset",
    "/Users/doge/Documents/Examples/lazega_nodes.tsv",
    type="nodeset",
)

lazega = th.load_file(
    "lazega",
    "/Users/doge/Documents/Examples/lazega.tsv",
    type="network",
)

th.info(lazega)

th.shortest_path("lazega", 1, 23, "advice")

client.stop()
```