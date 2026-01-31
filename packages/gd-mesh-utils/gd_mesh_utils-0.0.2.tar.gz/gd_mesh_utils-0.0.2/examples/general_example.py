import logging
import numpy as np
import matplotlib.pyplot as plt

import gdutils as gd
import gdmesh as gm


def main():
    out = gd.fPath(__file__, "out")

    with gd.Container(out) as ct:


    log.info(f"")


log = logging.getLogger(__name__)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    log = gd.get_logger()

    main()
