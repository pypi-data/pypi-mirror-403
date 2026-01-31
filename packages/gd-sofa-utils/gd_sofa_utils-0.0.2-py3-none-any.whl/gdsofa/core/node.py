from __future__ import annotations

from dataclasses import dataclass
import json
import logging
import os
import re
from pathlib import Path
from typing import Callable, Generator
from typing import List
from typing import TYPE_CHECKING

from colour import Color
from treelib import Tree

import gdutils as gd
from gdsofa.core.links import Link, MultiLink
from gdsofa.utils import (
    JsonEncoder,
    as_iterable,
    dump_path,
    load_json,
    make_string,
    none_default,
    unique_id,
)
from gdsofa.utils import random_name

if TYPE_CHECKING:
    from gdsofa.core.component import Object

log = logging.getLogger(__name__)


class Node:
    """
    Implementation of a tree node

    A node contains a parent (except the root node) and two containers for its own components and for its child nodes.
    """

    def __init__(self, name, parent: Node = None, gravity=None, **kwargs):
        self.name = name
        self.bbox: BBOX = None
        self.gravity = none_default(gravity, [0, 0, 0])
        self.node_args = kwargs
        self.parent = parent
        self.children: List[Node] = []
        self.objs: List[Object] = []

    def __truediv__(self, other):
        return Path(str(self.path).lstrip("@")) / other

    def get_root(self):
        x = self
        while x.parent is not None:
            x = x.parent
        return x

    def get_node(self, name: str) -> Node:
        for x in self.children:
            if x.name == name:
                return x
        for x in self.children:
            if y := x.get_node(name):
                return y
        return None

    @property
    def last(self):
        return self.objs[-1]

    @property
    def path(self) -> str:
        x, y = self, []
        while x.parent is not None:
            y.append(x.name)
            x = x.parent
        y = list(reversed(y))
        return f"@{'/'.join(y)}"

    def add_visual(self, *visual, color="grey"):
        """Create a simple visual child node"""
        from gdsofa.core.component import Object
        from gdsofa.comps.base_component import IdentityMapping, VisualStyle

        visu = self.add_child(f"visu__{(idx := random_name())}")
        visu + Object(
            "OglModel",
            src=Link(self.find(class_name="MechanicalObject")),
            topology=Link(
                self.find(callback=lambda x: "TopologyContainer" in x.class_name)
            ),
            color=Color(color).rgb,
            name=f"ogl__{idx}",
        )
        visu + VisualStyle(*visual, name=f"style__{idx}")
        visu + IdentityMapping()
        return visu

    def add_child(self, name, **kwargs):
        self.children.append(Node(name, parent=self, **kwargs))
        return self.children[-1]

    def _get_dict(self):
        m = {}
        for x in self.children:
            m[x.name] = x._get_dict()
        m["__objs"] = [x for x in self.objs]
        return m

    def tree(self, show_data=True):
        """Build tree for current node"""
        tree = Tree()
        tree.create_node(self.name, self.name)  # root node

        def walk_dict(d, anchor="root"):
            for k, v in d.items():
                anc = unique_id()
                if k != "__objs":
                    s = f"{k}"  # Display node
                    tree.create_node(s, anc, parent=anchor)
                else:
                    for y in v:
                        y: Object
                        s = f"{y.class_name}"  # Display component
                        if y.name is not None:
                            s += f" ({y.name})"
                        a2 = unique_id()
                        tree.create_node(s, a2, parent=anchor)

                        if show_data:
                            for k2, v2 in y.kw.items():
                                if k2 not in ("name",):
                                    s = f"{k2}={v2}"
                                    tree.create_node(s, unique_id(), parent=a2)

                if isinstance(v, dict):
                    walk_dict(v, anchor=anc)

        walk_dict(self._get_dict())
        return tree

    def update_links(self):
        for x in self.children:
            x.update_links()
        for x in self.objs:
            for k, v in x.kw.items():
                if isinstance(v, (Link, MultiLink)):
                    x.kw[k] = v.resolve(context=self)

    def _to_file(self, parent_node):
        s = ""
        conv = lambda x: json.loads(json.dumps(x, cls=JsonEncoder))
        wrap = lambda x: x if isinstance(x, (float, list, dict)) else f"'{x}'"
        rr = lambda x: ", ".join([f"{k}={wrap(v)}" for k, v in conv(x).items()])
        if parent_node.name == "root":
            if self.gravity is not None:
                s += f"\t{parent_node.name}.gravity.value = {self.gravity}\n"

            if len(parent_node.node_args) > 0:
                for k, v in conv(parent_node.node_args).items():
                    s += f"\t{parent_node.name}.{k}.value = {v!r}\n"

        if self.bbox is not None:
            s += f"\t{parent_node.name}.bbox.value = '{self.bbox.value}'\n"
        for x in self.objs:
            kw = f", {rr(x.kw)}" if len(x.kw) > 0 else ""
            s += f"\t{parent_node.name}.addObject('{x.class_name}'{kw})\n"
        for x in self.children:
            kw = f", {rr(x.node_args)}" if len(x.node_args) > 0 else ""
            s += f"\n\t{x.name} = {parent_node.name}.addChild('{x.name}'{kw})\n"
            s += x._to_file(x)
        return s

    def to_file(self, fname, clean_paths=False, doc=None):
        from gdsofa.comps import RequiredPlugin

        plgn_node = self.add_child("RequiredPlugins")
        for x in self.build_plugins_list():
            if not self.find("RequiredPlugin", name=x, silent=True):
                obj = RequiredPlugin(name=x)
                obj.parent = plgn_node
                plgn_node.objs.append(obj)

        self.update_links()
        SOFA_EXE = Path(os.environ.get("SOFA_ROOT", "")) / "bin/runSofa"
        _link = "https://gdutils-a2ef81.gitlabpages.inria.fr/"
        s = f"# This file implements a SOFA-framework simulation scene, generated with [gd-sofa-utils]({_link})\n"
        s += f"# runSofa -l SofaPython3 {Path(fname).name}\n"
        s += f"# {SOFA_EXE} -l SofaPython3 {Path(fname).resolve()}\n"

        if doc is not None:
            docs = doc.split("\n")
            s += "\n"
            for x in docs:
                s += f"# {x}\n"

        s += "\n\ndef createScene(root):\n"
        s += self._to_file(self)

        if clean_paths:
            cpath = os.path.commonpath(re.findall(r'\/[^\s,"\']+\.\w+', s))
            s = s.replace(cpath + "/", "")

        try:
            p = Path(fname)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(s, encoding="utf-8")
        except Exception as e:
            log.error(f"Could not write scene to file: {e}")
        else:
            gd.get_logger().info(f"Written: {fname}")

    def build_plugins_list(self):
        from gdsofa.comps import REQUIRED_PLUGINS

        d = dict(REQUIRED_PLUGINS)
        pl = []
        for x in self.up2down:
            if x.class_name in d:
                pl.append(d[x.class_name])
                del d[x.class_name]
            elif x.class_name == "RequiredPlugin":
                pl.append(x.name)
        self.imported_plugins = pl
        return pl

    def to_dict(self):
        return self.tree().to_dict(sort=False)

    def print(self, show_data=True):
        self.update_links()
        self.tree(show_data).show(key=False)
        return self

    def dump_tree(self, fname: str = None):
        fname = Path(none_default(fname, "."))
        if fname.is_dir():
            fname = fname / "tree.txt"
        fname = Path(fname)
        fname.unlink(missing_ok=True)
        self.tree().save2file(str(fname))
        gd.get_logger().info(f"Written: {fname}")

    def add(self, other):
        for y in as_iterable(other):
            if isinstance(y, Node):
                y.parent = self
                self.children.append(y)
            else:
                y.attach_to(self)
        return other

    def __add__(self, other):
        return self.add(other)

    def _add_sofa(self, parent_node):
        if self.gravity is not None:
            parent_node.gravity.value = self.gravity
        if self.bbox is not None:
            parent_node.bbox.value = self.bbox.value
        for x in self.objs:
            try:
                parent_node.addObject(x.class_name, **x.kw)
            except Exception as e:
                log.error(
                    f"Error creating {x.class_name!r} in node {parent_node.name.value!r}"
                )
                raise e
        for x in self.children:
            n = parent_node.addChild(x.name, **x.node_args)
            x._add_sofa(n)

    def to_sofa(self):
        from Sofa.Core import Node as SofaNode

        root = SofaNode("root")
        self.update_links()
        self._add_sofa(root)

        return root

    def path_from(self, node: Node) -> str:
        """
        Return the relative path between 2 nodes
        :param node: the starting node
        """
        spl = lambda x: as_iterable(x[1:].split("/"))
        a, b = spl(self.path), spl(node.path)
        if a == b:
            return "@"
        i = -1
        s = Path()
        j = -1
        for ej, (ea, eb) in enumerate(zip(a, b)):
            if ea == eb:
                j = ej
        if j >= 0:
            a = a[j + 1:]
            b = b[j + 1:]
        for x in list(reversed(b)):
            if len(x) > 0:
                if x in a:
                    i = a.index(x)
                else:
                    s = s / ".."
        for x in a[i + 1:]:
            s = s / x
        return f"@{s}"

    @property
    def nodes_up2down(self):
        """
        Generator that browses the scene graph nodes from current node to leaves.
        """
        yield self
        for child in self.children:
            yield from child.nodes_up2down

    @property
    def up2down(self):
        """
        Generator that browses the node's objects from current node to down
        """
        for x in self.objs:
            yield x
        for x in self.children:
            for y in x.up2down:
                yield y

    @property
    def down2up(self):
        """
        Generator that browses the node's objects from current node to root
        """
        for x in self.objs:
            yield x
        if self.parent:
            for y in self.parent.down2up:
                yield y

    def _find(
        self,
        class_name: str = None,
        name: str = None,
        callback: Callable = None,
        direction: Generator = None,
        silent=False,
    ):
        direction = none_default(direction, self.up2down)
        infos = {}
        if callback is None:
            if name is not None:
                infos["name"] = name
                callback = lambda x: x.name == name
            elif class_name is not None:
                infos["class_name"] = class_name
                callback = lambda x: x.class_name == class_name
            else:
                raise RuntimeError("At least one argument must be set")
        infos["callback"] = callback
        for x in direction:
            if callback(x):
                return x
        if not silent:
            j = make_string(**infos)
            log.error((m := f"Object {j!r} not found in the {self.name} node"))
            raise KeyError(m)

    def find(
        self,
        class_name: str = None,
        name: str = None,
        callback: Callable = None,
        silent=False,
    ):
        """Find the first object that satisfies `Callable(object) == True`"""
        return self._find(
            class_name, name, callback, direction=self.up2down, silent=silent
        )

    def rfind(
        self,
        class_name: str = None,
        name: str = None,
        callback: Callable = None,
        silent=False,
    ):
        """Similar to find, but from current node to root"""
        return self._find(
            class_name, name, callback, direction=self.down2up, silent=silent
        )

    def set_bbox(self, val: str | list | tuple, fmt="xmin_ymin"):
        # fmt: xmin_ymin or xmin_xmax
        if isinstance(val, str):
            _bbox = val.split(" ")
        elif isinstance(as_iterable(val), (list, tuple)):
            _bbox = list(map(float, val))
        else:
            raise NotImplementedError

        if fmt == "xmin_ymin":
            self.bbox = BBOX(
                min=[_bbox[0], _bbox[1], _bbox[2]], max=[_bbox[3], _bbox[4], _bbox[5]]
            )
        elif fmt == "xmin_xmax":
            self.bbox = BBOX(
                min=[_bbox[0], _bbox[2], _bbox[4]], max=[_bbox[1], _bbox[3], _bbox[5]]
            )
        else:
            raise NotImplementedError


@dataclass
class BBOX:
    min: list[float]
    max: list[float]

    @property
    def value(self):
        return (
            " ".join(map(str, map(float, self.min)))
            + " "
            + " ".join(map(str, map(float, self.max)))
        )
