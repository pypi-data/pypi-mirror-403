# User guide

## Requirements

gdsofa requires a SOFA build. Set the **`SOFA_ROOT`** environment variable to your SOFA build directory (the path that contains `lib/python3/site-packages` or `lib/python/site-packages`). The library uses it to extend `sys.path` and load SOFA’s Python bindings.

```bash
export SOFA_ROOT=/path/to/sofa/build
```

If `SOFA_ROOT` is missing, `load_SOFA()` and `RunSofa` will raise an error.

gdsofa also depends on [gdutils](https://gdutils-a2ef81.gitlabpages.inria.fr/) for JSON I/O, timing, and iterable helpers (see [Utilities](#utilities)).

## Scene graph

The scene is a tree of **nodes**. Each node can have child nodes and **components** (SOFA objects).

### Root and nodes

- **`RootNode(**kw)`** — Creates the root node of the scene and adds a default visual manager loop. Use this as the top-level node.
- **`Node(name, parent=None, gravity=None, **kwargs)`** — Creates a child node. You typically create children with **`parent.add_child(name, **kwargs)`**.
- Add components to a node with **`node + component`** (e.g. `root + DefaultAnimationLoop()`).

Example:

```python
import gdsofa as gs

root = gs.RootNode()
root + gs.DefaultAnimationLoop()

# Add a child node and components
child = root.add_child("my_node")
child + gs.MechanicalObject()
# ... more components
```

### Core types

- **Components** — Use the classes from `gdsofa.comps` (e.g. `DefaultAnimationLoop`, `MechanicalObject`, `EulerImplicitSolver`, `MeshVTKLoader`, `Gravity`). They are added to nodes with `+`.
- **Links** — Use `Link` and `MultiLink` from `gdsofa.core` to reference other components (e.g. for mappings or loaders).
- **Objects** — For custom SOFA types, use `Object(class_name, **kwargs)` from `gdsofa.core`.

## Parameters

**`BaseSOFAParams`** holds simulation and I/O settings. Main attributes:

- **`out_dir`** — Output directory (created if missing).
- **`n`** — Number of iterations (default 100).
- **`dt`** — Time step (default 1; often overridden, e.g. 0.005).
- **`scale`** — Scaling for SOFA loaders.
- **`data_path`** — Optional data input directory.

You can load/save parameters as JSON:

- **`params.dump_json(fname)`** / **`params.save()`** — Write current parameters (e.g. to `out_dir/params.json`).
- **`BaseSOFAParams.from_json(fname)`** / **`BaseSOFAParams.from_dir(dname)`** — Load from file or from a directory containing `params.json`.

Example:

```python
params = gs.BaseSOFAParams(out_dir="/path/to/out", n=200, dt=0.005)
params.save()
# later:
params = gs.BaseSOFAParams.from_dir("/path/to/out")
```

## Controllers

Custom logic per time step is done with **controllers**. Subclass **`BaseSOFAController`** and override:

- **`before_animate(ctx)`** — Called before each simulation step.
- **`after_animate(ctx)`** — Called after each step.

The controller receives `root` (the gdsofa root node) and `params` (the `BaseSOFAParams` instance). Use `self.get_node(name)` and `self.root.find(...)` to reach nodes and components.

Pass controller **classes** (not instances) to **`RunSofa`**:

```python
class MyController(gs.BaseSOFAController):
    def after_animate(self, ctx):
        # e.g. log or export data
        pass

sofa = gs.RunSofa(root, params, MyController)
sofa.run(gui=False)
```

## Running

**`RunSofa(root, params=None, *controllers)`** builds the SOFA scene from the gdsofa graph and optionally attaches controllers.

- **`params`** — Optional. If omitted, a default `BaseSOFAParams()` is used (you should set at least `out_dir` for file output).
- **`*controllers`** — Optional controller classes.

Methods:

- **`run(gui=False, std_to_file=False, viewer="qglviewer", title="MyProject")`** — Runs the simulation.
  - **`gui=True`** — Opens the SOFA GUI (requires Qt and SOFA GUI plugins).
  - **`gui=False`** — Headless: runs `n` steps (from `params`).
  - **`std_to_file=True`** — Redirects stdout/stderr to files under `params.out_dir` (requires `out_dir` set).
- **`to_file(fname=None, clean_paths=False, doc=None)`** — Exports the scene as a Python script. Default path is `params.out_dir/sofa_scene.py` if `out_dir` is set.
- **`import_plugins()`** — Called during `__init__`; imports SOFA plugins required by the scene graph.

Example (headless with output directory):

```python
params = gs.BaseSOFAParams(out_dir="/path/to/out", n=100, dt=0.005)
sofa = gs.RunSofa(root, params)
result = sofa.run(gui=False, std_to_file=True)
result.save()  # writes run_stats.json under out_dir
sofa.to_file() # writes sofa_scene.py under out_dir
```

## Utilities

**`gdsofa.utils`** provides helpers used internally and available for your scripts:

- **From [gdutils](https://gdutils-a2ef81.gitlabpages.inria.fr/)**: `load_json`, `dump_json`, `Timer`, and `as_iterable` (alias of gdutils’ `get_iterable`). gdsofa re-exports these to avoid redundancy; see the gdutils docs for full details.
- **gdsofa-specific**: `dump_path` (create directory and return path), `Munch` / `munchify` (dict with attribute access), `JsonEncoder` (Path and numpy in JSON), `StdRedirect`, and helpers such as `ensure_ext`, `path_insert_before`, `random_name`, `unique_id`.

For path management relative to your script (e.g. output directories), you can use **`gd.fPath(__file__, "out", mkdir=True)`** from gdutils directly.
