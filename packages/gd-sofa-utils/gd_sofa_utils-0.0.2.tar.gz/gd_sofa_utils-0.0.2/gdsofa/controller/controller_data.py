import logging

import pandas as pd


class ControllerData(list):
    def __init__(self, parent: "BaseSOFAController"):
        super().__init__()
        self.parent = parent

    def add(self, **kw):
        kw.setdefault("t", self.parent.t)
        kw.setdefault("dt", self.parent.dt)
        kw.setdefault("iter", self.parent.iter)
        self.append(kw)

    @property
    def df(self):
        return pd.DataFrame(self)


log = logging.getLogger(__name__)
