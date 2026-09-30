"""Animated version of the lumped-model chart for the video -> sim1_lumped_animation.mp4"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FFMpegWriter
from milkshield_sim import simulate

INK, INK2 = "#0b0b0b", "#52514e"
cases = [("Fresh 40 L, 8 cartridges", 40, 8, 35.0, "#2a78d6"),
         ("Fresh 30 L, 6 cartridges", 30, 6, 35.0, "#eb6834"),
         ("Pre-chilled 40 L, 2 cartridges", 40, 2, 6.0, "#1baf7a"),
         ("Plain can, no ice", 40, 0, 35.0, INK2)]
runs = [simulate(L, n, T0, hours=12.0) for _, L, n, T0, _ in cases]
t = runs[0][0]
fig, ax = plt.subplots(figsize=(12.8, 7.2), dpi=100)
fig.subplots_adjust(left=0.08, right=0.74, bottom=0.12, top=0.88)
writer = FFMpegWriter(fps=24, bitrate=3000)
N = 240
with writer.saving(fig, "sim1_lumped_animation.mp4", dpi=100):
    for f in list(range(1, N + 1)) + [N] * 48:          # 10 s draw + 2 s hold
        k = int(len(t) * f / N) - 1
        ax.clear()
        ax.axhspan(4, 8, color="#1baf7a", alpha=0.10, lw=0)
        ax.text(11.9, 8.6, "4-8 °C target", ha="right", fontsize=10, color=INK2)
        for (lab, *_ , c), (tt, T, _) in zip(cases, runs):
            ax.plot(tt[:k+1], T[:k+1], color=c, lw=2.5)
            ax.plot(tt[k], T[k], "o", color=c, ms=8, mec="white", mew=2)
        ys = [5.2, 8.2, 2.2, 35]            # ordered like the 12 h end values
        for (lab, *_, c), y in zip(cases, ys):
            ax.plot([12.15, 12.5], [y, y], color=c, lw=3, clip_on=False)
            ax.text(12.6, y, lab, va="center", fontsize=11, color=INK)
        ax.set_xlim(0, 12); ax.set_ylim(0, 37); ax.set_xticks(range(0, 13, 2))
        ax.set_xlabel("Hours after sealing", fontsize=12); ax.set_ylabel("Milk temperature (°C)", fontsize=12)
        ax.set_title(f"MilkShield thermal model, 35 °C day   t = {t[k]:4.1f} h", loc="left", fontsize=14)
        ax.grid(axis="y", color="#e6e5e0", lw=0.8); ax.set_axisbelow(True)
        for s in ("top", "right"): ax.spines[s].set_visible(False)
        fig.texts.clear()
        fig.text(0.08, 0.02, "Lumped thermal model, assumed inputs. Design estimate, not test data.", fontsize=9, color=INK2)
        writer.grab_frame()
print("saved sim1_lumped_animation.mp4")
