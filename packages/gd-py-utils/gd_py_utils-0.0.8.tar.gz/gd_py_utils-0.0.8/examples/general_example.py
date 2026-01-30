import logging
import numpy as np
import matplotlib.pyplot as plt

import gdutils as gd


def main():
    out = gd.fPath(__file__, "out", mkdir=True)

    with gd.Container(out) as ct:
        t = np.linspace(0, 2 * np.pi, 200)
        y = np.sin(t)

        with gd.SPlot(ct / "sin_plot.png", show=False):
            fig, ax = plt.subplots()
            ax.plot(t, y, label="sin(t)")

            ax.set_xlabel("t")
            ax.set_ylabel("Amplitude")
            ax.set_title("Sinus de t")
            ax.legend()

            gd.despine(ax=ax, trim=True)
            gd.move_legend(ax, loc="upper right")

    log.info(f"Plot generated and saved to {ct.sin_plot}")


log = logging.getLogger(__name__)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    log = gd.get_logger()

    main()
