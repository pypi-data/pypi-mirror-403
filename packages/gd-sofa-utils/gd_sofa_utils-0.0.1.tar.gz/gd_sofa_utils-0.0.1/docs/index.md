# gdsofa

**gdsofa** is a lightweight Python library for building and running [SOFA](https://www.sofa-framework.org/) (Simulation Open Framework Architecture) scenes programmatically. It provides a scene graph API (nodes, components, parameters, controllers) and a runner for headless or GUI simulations.

## Requirements

- Python 3.12 (same as SOFAPython3 version)
- A SOFA build: set the **`SOFA_ROOT`** environment variable to your SOFA build directory.

## Installation

```bash
pip install gd-sofa-utils
```

## Quick start

Build a minimal scene, attach parameters, and run it (GUI or headless):

```python
import gdsofa as gs

root = gs.RootNode()
root + gs.DefaultAnimationLoop()

params = gs.BaseSOFAParams(out_dir="/path/to/out")
sofa = gs.RunSofa(root, params)
sofa.run(gui=True)
```

Next steps:

- [User guide](guide.md) — requirements, scene graph, parameters, controllers, running.
- [API Reference](api.md) — full API documentation.
