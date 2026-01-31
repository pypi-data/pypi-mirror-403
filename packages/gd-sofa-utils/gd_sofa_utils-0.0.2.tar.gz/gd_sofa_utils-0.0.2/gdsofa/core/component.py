import logging
from copy import deepcopy
from pathlib import Path

from gdsofa.core.links import Link, MultiLink
from gdsofa.core.node import Node
from gdsofa.utils import Munch, munchify, random_name

log = logging.getLogger(__name__)


class Object:
    """
    Class representing a SOFA component. The component's data is stored in the `kw` attribute.
    """

    def __init__(self, class_name, **kw):
        self.class_name = class_name
        # Do not munchify Link/MultiLink - they are list subclasses and would be turned into generators
        self.kw = Munch({k: v if isinstance(v, (Link, MultiLink)) else munchify(v) for k, v in kw.items()})
        self.parent = None

        if self.name is None:
            self.name = f"{class_name}__{random_name()}"

    @property
    def name(self):
        return self.kw.get("name")

    @name.setter
    def name(self, value):
        self.kw["name"] = value

    def attach_to(self, node: Node):
        self.parent = node
        node.objs.append(self)

    @property
    def path(self) -> str:
        if self.parent is None:
            raise RuntimeError("Component is not attached to any scene")
        p = str(self.parent.path)
        if p == "@":
            return f"@{self.name}"
        return f"{p}/{self.name}"

    def __call__(self, **kw):
        c = deepcopy(self)
        c.kw.update(kw)
        return c


class TObject(Object):
    """
    Object whose SOFA class is guessed from the python class name
    """

    def __init__(self, **kw):
        super().__init__(self.__class__.__name__, **kw)
