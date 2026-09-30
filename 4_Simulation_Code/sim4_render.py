"""Render cfd_frames.npz -> sim4_cfd_convection.mp4 + sim4_cfd_snapshots.png"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle
from matplotlib.animation import FFMpegWriter
from milkshield_sim import simulate

d = np.load("cfd_frames.npz")
T, PSI, t = d["T"], d["psi"], d["t"]
x, z, obst = d["x"] * 1000, d["z"] * 1000, d["obst"]
mean, top, bot = d["mean"], d["top"], d["bot"]
tl, Tl, _ = simulate(40, 8, hours=2.0)          # lumped model, same case, for comparison
cmap = LinearSegmentedColormap.from_list("coldhot", ["#1c5cab", "#8fb8e8", "#f2f1ec", "#f0a57d", "#c2410c"])
INK, INK2 = "#0b0b0b", "#52514e"
CARTS = [(30, 110), (290, 370)]

def draw_field(ax, k, labels=True):
    f = np.where(obst, np.nan, T[k])
    ax.imshow(f, origin="lower", cmap=cmap, vmin=0, vmax=35, extent=[0, 400, 0, 512], interpolation="bilinear")
    p = PSI[k]; lim = np.abs(p).max()
    if lim > 1e-9:
        lev = np.linspace(-lim, lim, 16); lev = lev[np.abs(lev) > lim * 0.04]
        ax.contour(x, z, p, levels=lev, colors=INK, linewidths=0.6, alpha=0.55, negative_linestyles="solid")
    for a, b in CARTS:
        ax.add_patch(Rectangle((a, 112), b - a, 400, fc="#dfe7ef", ec=INK, lw=1))
        if labels: ax.text((a + b) / 2, 330, "ICE\n0 °C", ha="center", va="center", fontsize=9, color=INK)
    ax.set_xlim(0, 400); ax.set_ylim(0, 512); ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values(): s.set_color(INK2)

if __name__ == "__main__":
    fig = plt.figure(figsize=(12.8, 7.2), dpi=100)
    ax = fig.add_axes([0.04, 0.10, 0.36, 0.78]); cax = fig.add_axes([0.41, 0.18, 0.012, 0.62])
    ax2 = fig.add_axes([0.52, 0.14, 0.43, 0.70])
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(0, 35)); cb = fig.colorbar(sm, cax=cax)
    cb.set_label("Milk temperature (°C)")
    writer = FFMpegWriter(fps=20, bitrate=4000)
    with writer.saving(fig, "sim4_cfd_convection.mp4", dpi=100):
        for k in range(len(t)):
            ax.clear(); ax2.clear()
            draw_field(ax, k)
            ax.set_title(f"Inside the can (side slice)   t = {t[k]/60:4.0f} min", loc="left", fontsize=13)
            ax.text(0, -22, "lines = milk circulation (streamlines)", fontsize=9, color=INK2)
            ax2.axhspan(4, 8, color="#1baf7a", alpha=0.10, lw=0)
            ax2.plot(tl * 60, Tl, color=INK2, lw=1.5, ls="--")
            ax2.plot(t[:k+1] / 60, top[:k+1], color="#eb6834", lw=2)
            ax2.plot(t[:k+1] / 60, mean[:k+1], color="#2a78d6", lw=2.5)
            ax2.plot(t[:k+1] / 60, bot[:k+1], color="#1baf7a", lw=2)
            ax2.set_xlim(0, 120); ax2.set_ylim(0, 36); ax2.set_xlabel("Minutes after sealing"); ax2.set_ylabel("°C")
            ax2.grid(axis="y", color="#e6e5e0", lw=0.8); ax2.set_axisbelow(True)
            for s in ("top", "right"): ax2.spines[s].set_visible(False)
            ax2.set_title("Milk temperature: top / average / bottom", loc="left", fontsize=13)
            y0 = 33
            for lab, c, ls in (("top 100 mm of milk", "#eb6834", "-"), ("average (CFD)", "#2a78d6", "-"),
                               ("bottom 100 mm of milk", "#1baf7a", "-"), ("average (lumped model)", INK2, "--")):
                ax2.plot([72, 78], [y0, y0], color=c, lw=2.5, ls=ls); ax2.text(80, y0, lab, va="center", fontsize=10)
                y0 -= 2.6
            ax2.text(119, 8.5, "4-8 °C target", ha="right", fontsize=9, color=INK2)
            fig.texts.clear()
            fig.text(0.04, 0.025, "2D CFD, effective (eddy) viscosity, Ra_eff 1e6, 8-cartridge can, 35 °C. "
                     "Flow pattern is the output; timing depends on assumptions. Design estimate, not test data.",
                     fontsize=9, color=INK2)
            writer.grab_frame()
    plt.close(fig)

    # snapshot strip for slides
    picks = [int(np.argmin(np.abs(t - s * 60))) for s in (2, 15, 45, 110)]
    fig, axs = plt.subplots(1, 4, figsize=(14, 5.4), dpi=150)
    for a, k in zip(axs, picks):
        draw_field(a, k, labels=False)
        a.set_title(f"{t[k]/60:.0f} min  (avg {mean[k]:.1f} °C)", fontsize=12)
    fig.subplots_adjust(left=0.01, right=0.9, top=0.84, bottom=0.03, wspace=0.08)
    cax2 = fig.add_axes([0.92, 0.1, 0.012, 0.68])
    fig.colorbar(sm, cax=cax2).set_label("Milk temperature (°C)")
    fig.suptitle("Cold milk runs down the ice, sweeps the floor and rises through the centre: a self-stirring loop (2D CFD)",
                 x=0.02, ha="left", fontsize=13)
    fig.savefig("sim4_cfd_snapshots.png", bbox_inches="tight"); plt.close(fig)
    print("saved sim4_cfd_convection.mp4 and sim4_cfd_snapshots.png")
