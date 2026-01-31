from __future__ import annotations

import logging
from typing import List
from typing import TYPE_CHECKING

from gdsofa.utils import as_iterable, random_name

if TYPE_CHECKING:
    from gdsofa.core.component import Object
    from gdsofa.core.node import Node

log = logging.getLogger(__name__)


class Link:
    """
    Implementation of a link between two components
    """

    def __init__(self, obj: Object, attr: str = None):
        if obj is None:
            log.error((m := "The linked object is None"))
            raise RuntimeError(m)

        self.obj = obj
        self.attr = attr

    def resolve(self, context: Node = None):
        """
        Convert the Link object to a string representing the relative path from the current
        context (or the root node by default) to the object `self.obj`
        """
        if self.obj.name is None:
            self.obj.name = f"{self.obj.class_name}__{random_name()}"
        if context:
            s = self.obj.parent.path_from(context)
            if len(s) > 1 and not s.endswith("/"):
                s += "/"
            s += self.obj.name
        else:
            s = str(self.obj.path)
        if self.attr:
            s += f".{self.attr}"
        return s


class MultiLink(List[Link]):
    """
    Implementation of a multi link, which is a list of single links
    """

    def __init__(self, *a):
        super().__init__([Link(*as_iterable(x)) for x in a])

    def resolve(self, context: Node = None):
        return [x.resolve(context) for x in self]


class MultiLinkExporter(MultiLink):
    """
    MultiLink for VTKExporter
    """

    def resolve(self, context: Node = None):
        return [f"{x.attr}={x.resolve(context)}" for x in self]
