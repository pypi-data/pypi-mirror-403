import logging
import re
from pathlib import Path

import gdutils as gd
from gdsofa import *

# bien penser à commenter `from SofaModel.comps._dyn import *` pour faire tourner ce fichier
# (se base sur globals())

def main(force=True):
    out = tf.f(__file__, "out", dump=True)
    root = Path(tf.env("SOFA_ROOT") / "Sofa")

    def g(r):
        fnames = []
        for x in (root / r).rglob("build.make"):
            if (y := x.parent.name).endswith(".dir"):
                if not y[:-4].endswith("_test"):
                    fnames.append({"a": str(x), "b": y[:-4]})
        return fnames

    def extract_cpp_objects(info):
        filepath = info["a"]
        cpp_names = set()
        pattern = re.compile(r"/([^/]+)\.cpp\.o")
        with open(filepath, "r") as f:
            for line in f:
                match = pattern.search(line)
                if match:
                    name = re.sub(r"\[.*\]", "", match.group(1))  # Remove anything like [GraphScattered]
                    if name and name[0].isupper():
                        cpp_names.add(name)
        return {"info": info["b"], "reqs": sorted(cpp_names)}

    if tf.greedy_download(fname := out / "fnames.json", force=force):
        tf.dump_json(fname, {"Component": g("Component"), "GL": g("GL")})
    fnames = tf.load_json(fname)

    if tf.greedy_download(fname_objs := out / "objs.json", force=force):
        objs = []
        for xx in fnames["Component"]:
            objs.append(extract_cpp_objects(xx))
        for xx in fnames["GL"]:
            objs.append(extract_cpp_objects(xx))
        tf.dump_json(fname_objs, objs)
    objs = tf.load_json(fname_objs)
    # pprint(objs)

    if tf.greedy_download(fname_2 := out / "dyn.py", force=force):
        glb = globals()
        s = "from SofaModel.core.component import TObject\n\n__all__ = [\n"
        s += f'\t"REQUIRED_PLUGINS",\n'
        for x in objs:
            # s +=
            for comp in x["reqs"]:
                if comp not in glb:
                    s += f'\t"{comp}",\n'
        s += "]\n\n\n"

        for x in objs:
            for comp in x["reqs"]:
                if comp not in glb:
                    s += f"class {comp}(TObject):\n\tpass\n\n"

        s += "REQUIRED_PLUGINS = {\n"
        for x in objs:
            for comp in x["reqs"]:
                s += f'\t"{comp}": "{x['info']}",\n'
        s += "}\n"

        gd.dump_str(fname_2, s)


log = logging.getLogger(__name__)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    log = gd.get_logger()

    main()
