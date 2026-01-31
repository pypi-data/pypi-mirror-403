"""
Thin wrapper for SOFA scene root and runner.
"""
import logging
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Union

from gdsofa.controller.controller import BaseSOFAController
from gdsofa.core.node import Node
from gdsofa.load_SOFA import load_SOFA
from gdsofa.sofa_parameters import BaseSOFAParams
from gdsofa.utils import StdRedirect, Timer, as_iterable, dump_json, none_default

log = logging.getLogger(__name__)


def RootNode(**kw) -> Node:
    """
    Create the root node of the scene graph.
    """
    from gdsofa.comps.base_component import DefaultVisualManagerLoop

    node = Node("root", **kw)
    node + DefaultVisualManagerLoop()
    return node


@dataclass
class SimulationResult:
    params: BaseSOFAParams
    comp_time_s: float

    def save(self):
        x = asdict(self)
        x.pop("params")
        path = Path(self.params.out_dir) / "run_stats.json"
        dump_json(path, x)


class RunSofa:
    """
    Util class to run a scene.
    """

    def __init__(
        self,
        root: Node,
        params: Union[BaseSOFAParams, None] = None,
        *controllers: Union[BaseSOFAController, List[BaseSOFAController]],
    ):
        if not os.environ.get("SOFA_ROOT"):
            raise RuntimeError("SOFA_ROOT environment variable is required")
        load_SOFA()

        self.params = none_default(params, BaseSOFAParams())
        self.root = root

        self.import_plugins()

        self.sofa_root = root.to_sofa()

        self.controllers = {}
        self.sofa_controllers = {}

        xt = as_iterable(controllers)
        if len(xt) > 0:
            for ctrl in xt:
                self.controllers[ctrl.__name__] = lxt = ctrl(self.root, self.params)
                self.sofa_controllers[ctrl.__name__] = lxst = lxt.to_SOFA(
                    self.sofa_root
                )
                self.sofa_root.addObject(lxst)

    def run(
        self,
        gui: bool = False,
        std_to_file: bool = False,
        viewer: str = "qglviewer",
        title: str = "MyProject",
    ) -> SimulationResult:
        from Sofa import Simulation  # type: ignore[import-untyped]

        def _p(key: str, default):
            return self.params[key] if key in self.params else default

        n = int(_p("n", 100))
        dt = float(_p("dt", 0.005))
        self.sofa_root.setDt(dt)

        Simulation.initRoot(self.sofa_root)

        out_dir = None
        if "out_dir" in self.params:
            out_dir = Path(self.params["out_dir"])

        with Timer() as ts:
            if gui:
                from Sofa.Gui import GUIManager
                from SofaRuntime import importPlugin

                importPlugin("Sofa.Component")
                importPlugin("Sofa.GL.Component")
                importPlugin("Sofa.GUI.Component")
                importPlugin("Sofa.Qt")
                log.info("Available GUIs: %s", GUIManager.ListSupportedGUI())

                GUIManager.Init(title, viewer)
                GUIManager.createGUI(self.sofa_root, title)
                GUIManager.SetDimension(900, 700)
                GUIManager.MainLoop(self.sofa_root)
                GUIManager.closeGUI()
            else:
                log.info("Starting SOFA for %s iterations", n)
                if std_to_file:
                    if out_dir is None:
                        raise ValueError("out_dir required when std_to_file=True")
                    out = out_dir / "Output_Python.stdout"
                    err = out_dir / "Error_Python.stderr"
                    with StdRedirect(sys.stdout, out):
                        with StdRedirect(sys.stderr, err):
                            for _ in range(n):
                                Simulation.animate(self.sofa_root, dt)
                    log.debug("Finished writing std to file")
                else:
                    for _ in range(n):
                        Simulation.animate(self.sofa_root, dt)

        return SimulationResult(self.params, ts.secs)

    def import_plugins(self):
        """
        Check if plugins have to be imported by browsing the scene graph
        for components listed in REQUIRED_PLUGINS.
        """
        from SofaRuntime import importPlugin

        for x in self.root.build_plugins_list():
            importPlugin(x)

    def to_file(self, fname=None, clean_paths=False, doc=None):
        if fname is None:
            fname = Path(self.params.out_dir) / "sofa_scene.py"
        self.root.to_file(fname, clean_paths=clean_paths, doc=doc)

    def disable_sofa_logger(self):
        for x in self.root.up2down:
            if "printLog" in x.kw:
                x.kw["printLog"] = False
