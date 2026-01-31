import logging

import gdutils as gd
import gdsofa as gs


def main():
    out = gd.fPath(__file__, "out")

    root = gs.RootNode()
    root + gs.DefaultAnimationLoop()
    
    params = gs.BaseSOFAParams(out_dir=out)
    
    sofa = gs.RunSofa(root, params)
    sofa.run(gui=True)


log = logging.getLogger(__name__)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    log = gd.get_logger()

    main()
