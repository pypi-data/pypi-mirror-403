from dataclasses import asdict, dataclass
import json
import logging
from functools import cache

import numpy as np

import gdutils as gd
from gdsofa.controller.controller_data import ControllerData
from gdsofa.core.links import MultiLink, Link
from gdsofa.core.node import Node
from gdsofa.sofa_parameters import BaseSOFAParams
from gdsofa.utils import Munch, munchify

__all__ = [
    "Spring",
    "Springs",
    "BaseSOFAController",
]


@dataclass
class Spring:
    id0: int
    id1: int
    stiffness: float
    damping: float
    restLenght: float

    def to_string(self):
        return " ".join(map(str, asdict(self).values()))


class Springs(list[Spring]):
    def to_string(self):
        return " ".join([y.to_string() for y in self])


class BaseSOFAController:
    """
    This class is a pure python reimplementation of a SOFA controller. It provides read/write access to SOFA data

    You may override the callbacks `before_animate` and `after_animate` in a subclass.
    """

    def __init__(self, root: Node, params: BaseSOFAParams):
        self.root: Node = root
        self.params = params
        self.r = None

        self.iter = 0
        self.data = ControllerData(self)

        self.get_node = self.root.get_node
        self.find = self.root.find
        self.rfind = self.root.rfind

    def init(self):
        """SOFAController init"""
        pass

    def before_animate(self):
        """BeginAnimateEvent"""
        pass

    def after_animate(self):
        """EndAnimateEvent"""
        pass

    def after_init(self):
        """Event triggered after components `init`"""
        pass

    @property
    def t(self):
        return self.r.time.value

    @property
    def dt(self):
        return self.r.dt.value

    @property
    def T(self):
        return self.params.n * self.params.dt

    def _before_animate(self, event):
        self.before_animate()

    def _after_animate(self, event):
        self.after_animate()
        self.iter += 1

    def handle_event(self, event: Munch):
        """General purpose handler"""
        pass

    @cache
    def _check_links(self, path):
        if isinstance(path, str):
            return path
        if isinstance(path, (Link, MultiLink)):
            path = path.resolve()[1:].replace("/", ".")
        return path

    def get(self, path):
        _path = self._check_links(path)
        try:
            y = self.r[_path]
            try:
                return y.value if hasattr(y, "value") else y
            except Exception:
                return y
        except Exception as e:
            log.error(
                f"{e}(Could not get data): could not read {_path!r}, maybe path is wrong or component does not exist"
            )

    def get_link(self, *a):
        return self.get(Link(*a))

    def set(self, path, value):  # .findData(data)
        if isinstance(value, np.ndarray):
            value = value.tolist()
        self.r[self._check_links(path)].value = value

    def to_SOFA(self, sofa_root):
        from Sofa.Core import Controller as Ct

        class Controller(Ct):
            def init(s_):
                self.init()

            def onAnimateBeginEvent(s_, event):
                self._before_animate(event)

            def onAnimateEndEvent(s_, event):
                self._after_animate(event)

            def handle_event(s_, event):
                self.handle_event(munchify(event))

            def onSimulationInitDoneEvent(s_, e):
                return self.after_init()

            def onSimulationInitStartEvent(s_, e):
                return self.handle_event(e)

            def onSimulationInitTexturesDoneEvent(s_, e):
                return self.handle_event(e)

            def onSimulationStartEvent(s_, e):
                return self.handle_event(e)

            def onSimulationStopEvent(s_, e):
                return self.handle_event(e)

            def onKeypressedEvent(s_, e):
                return self.handle_event(e)

            def onKeyreleasedEvent(s_, e):
                return self.handle_event(e)

            def bwdInit(s_, e):
                return self.handle_event(e)

        self.r = sofa_root
        return Controller(self.r, name="controller")

    def plot(self):
        pass

    def get_json(self, s) -> dict:
        """
        Deserialize json data to python dictionnary
        """
        return json.loads(self.get(s))

    def get_map_real(self, s) -> Munch:
        """
        Cast SOFA data to python dictionnary `str:float`

        using MapReal = std::map<std::string, Real>;
        Data<MapReal> d_map_real;
        """
        lines, d = self.get(s).split("\n"), {}
        for x in lines:
            key, val = (y := x.split(" "))[0], y[1]
            d[key] = float(val)
        return munchify(d)

    def get_map_coord(self, s) -> Munch:
        """
        Cast SOFA data to python dictionnary `str:numpy array`

        using MapCoord = std::map<std::string, sofa::defaulttype::Vec3Types::Coord>;
        Data<MapCoord> d_map_coord;
        """
        lines, d = self.get(s).split("\n"), {}
        for x in lines:
            key, val = (y := x.split(" "))[0], y[1:4]
            d[key] = np.array(val, dtype=float)
        return munchify(d)

    def get_map_vec_real(self, s) -> Munch:
        """
        Cast SOFA data to python dictionnary `str:numpy array`

        using MapVecReal = std::map<std::string, sofa::defaulttype::Vec3Types::VecReal>;
        Data<MapVecReal> d_map_vec_real;
        """
        lines, d = self.get(s).split("\n"), {}
        for x in lines:
            key, val = (y := x.split(" "))[0], y[1:]
            d[key] = np.array(val, dtype=float)
        return munchify(d)

    def get_map_vec_coord(self, s) -> Munch:
        """
        Cast SOFA data to python dictionnary `str:numpy array`

        using MapVecCoord = std::map<std::string, sofa::defaulttype::Vec3Types::VecCoord>;
        Data<MapVecCoord> d_map_vec_coord;
        """
        lines, d = self.get(s).split("\n"), {}
        for x in lines:
            key, val = (y := x.split(" "))[0], y[1:]
            z = np.array(val, dtype=float)
            d[key] = z.reshape((len(z) // 3, 3))
        return munchify(d)

    get_map_vec_deriv = get_map_vec_coord

    def get_springs(self, s) -> Springs:
        """
        Cast SOFA data to python array

        Data<type::vector<LinearSpring<Real>>> d_springs;
        """
        data = self.get(s).getValueString().split(" ")
        springs = Springs()
        for i in range(0, len(data), 5):
            springs.append(
                Spring(
                    int(data[i]),
                    int(data[i + 1]),
                    float(data[i + 2]),
                    float(data[i + 3]),
                    float(data[i + 4]),
                )
            )
        return springs


log = logging.getLogger(__name__)
