import json
import logging
import shutil
from pathlib import Path
from typing import Union

import numpy as np
import param

import gdutils as gd

from gdsofa.utils import (
    dump_json,
    dump_path,
    ensure_ext,
    load_json,
    path_insert_before,
)

log = logging.getLogger(__name__)


class Filename(param.Filename):
    __slots__ = ["must_exist"]

    def __init__(self, default=None, must_exist=False, **params):
        self.must_exist = must_exist
        super().__init__(default, **params)

    def _resolve(self, path):
        if path is None:
            return
        p = Path(path)
        if self.must_exist:
            return str(super()._resolve(path))
        return str(p.resolve())

    def _validate(self, val):
        if isinstance(val, Path):
            val = str(val.resolve())
        return super()._validate(val)


class Foldername(param.Foldername):
    __slots__ = ["create_if_not_exist", "must_exist"]

    def __init__(
        self, default=None, create_if_not_exist=False, must_exist=False, **params
    ):
        self.create_if_not_exist = create_if_not_exist
        self.must_exist = must_exist
        super().__init__(default, **params)

    def _resolve(self, path):
        if path is None:
            return
        p = Path(path)
        if self.create_if_not_exist:
            x = dump_path(p)
        else:
            x = p.resolve()
        if self.must_exist:
            y = super()._resolve(str(x))
        else:
            y = str(x) if hasattr(x, "__str__") else str(Path(x).resolve())
        return Path(y)

    def _validate(self, val):
        if isinstance(val, Path):
            val = str(val.resolve())
        return super()._validate(val)


class BaseSOFAParams(param.Parameterized):
    title = param.String(
        default="SOFA Parameters",
        doc="`BaseSOFAParams` is a container for SOFA Parameters",
    )
    out_dir = Foldername(
        doc="Simulation output directory", create_if_not_exist=True, must_exist=False
    )
    data_path = Foldername(doc="Data input directory", must_exist=False)

    n = param.Integer(100, bounds=(0, np.inf), doc="Number of iterations")
    dt = param.Number(1, bounds=(0, np.inf), doc="Time step")
    scale = param.Number(
        1, bounds=(0, np.inf), doc="Scaling coefficient (for SOFA loaders)"
    )
    simu_dir = Foldername(doc="Simulation output directory")

    def update(self, *a, **kw):
        self.param.update(*a, **kw)

    def __len__(self):
        return len(list(self.param))

    def clean_simu_dir(self):
        p = Path(self.simu_dir)
        if p.is_dir():
            shutil.rmtree(p)
        dump_path(p)

    @staticmethod
    def _paths_to_serializable(obj):
        """Return a JSON-serializable copy of obj with Path replaced by absolute path str."""
        if isinstance(obj, Path):
            return str(obj.resolve())
        if isinstance(obj, dict):
            return {k: BaseSOFAParams._paths_to_serializable(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [BaseSOFAParams._paths_to_serializable(v) for v in obj]
        return obj

    def to_dict(self) -> dict:
        d = {name: getattr(self, name) for name in self.param}
        return self._paths_to_serializable(d)

    def dump_json(self, fname: str):
        fname = ensure_ext(fname, "json")
        dump_json(fname, self.to_dict())
        dump_json(path_insert_before(fname, ".json", "_schema"), self.param.schema())

    @classmethod
    def from_json(cls, fname: str):
        fname = ensure_ext(fname, "json")
        s = load_json(fname)
        return cls.from_dict(s)

    @classmethod
    def from_dict(cls, d: dict):
        x = cls().param
        for k, v in d.items():
            if not hasattr(x, k):
                if isinstance(v, float):
                    z = param.Number(v)
                elif isinstance(v, list):
                    z = param.List(v)
                else:
                    z = Filename(v)
                x.add_parameter(k, z)
        y = x.deserialize_parameters(json.dumps(d))
        return cls(**y)

    @param.depends("out_dir", watch=True, on_init=True)
    def _update_simu_dir(self):
        if self.out_dir is not None:
            self.simu_dir = str(dump_path(Path(self.out_dir) / "simu"))

    def save(self):
        self.dump_json(Path(self.out_dir) / "params.json")
        gd.get_logger().info(f"Written: {Path(self.out_dir) / 'params.json'}")

    @classmethod
    def from_dir(cls, dname):
        return cls.from_json(Path(dname) / "params.json")

    def __iter__(self):
        return self.param.__iter__()

    def __getitem__(self, item):
        return getattr(self, item)

    def __setitem__(self, key, value):
        return setattr(self, key, value)

    def add_container(self, ct: Union[gd.Container, str]):
        r = ct if isinstance(ct, gd.Container) else gd.Container(ct)
        self.data_path = str(r)
        keys = getattr(r, "get_file_keys", None)
        if callable(keys):
            for k in keys():
                self.param.add_parameter(k, Filename(getattr(r, k)))
        return self
