import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CREAM, BROWN, ACCENT, INK = "#f6f1ea", "#2a1f17", "#9a6b43", "#4a3b2f"

def style():
    plt.rcParams.update({
        "figure.facecolor": CREAM, "axes.facecolor": "#fffdfb",
        "axes.edgecolor": BROWN, "axes.labelcolor": BROWN,
        "axes.titlecolor": BROWN, "text.color": BROWN,
        "xtick.color": BROWN, "ytick.color": BROWN,
        "axes.grid": True, "grid.color": "#e6ddd2", "grid.linewidth": 0.6,
        "axes.spines.top": False, "axes.spines.right": False,
        "font.size": 11, "axes.titlesize": 13, "axes.titleweight": "bold",
        "font.family": "DejaVu Sans", "figure.dpi": 110,
    })
