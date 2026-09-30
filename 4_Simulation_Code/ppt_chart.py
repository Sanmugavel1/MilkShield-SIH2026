"""Compact chart for deck slide 3 (placed at 3.77 x 1.85 in)."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from milkshield_sim import simulate
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8.5})
NAVY, TEAL, SLATE = "#0B3C5D", "#1E8C7E", "#5B6B78"
t, T, _ = simulate(40, 8, hours=12.0)
t8 = t[np.argmax(T <= 8)]
fig, ax = plt.subplots(figsize=(3.77, 1.85), dpi=300)
fig.subplots_adjust(left=0.115, right=0.985, top=0.95, bottom=0.215)
ax.axhspan(0, 8, color=TEAL, alpha=0.10, lw=0)
ax.axhline(35, color=SLATE, lw=1.4, ls=(0, (4, 2)))
ax.text(11.9, 31.2, "Plain can, no cooling", ha="right", fontsize=7.5, color=SLATE)
ax.plot(t, T, color=NAVY, lw=2)
ax.plot([t8], [8], "o", color=TEAL, ms=4.5, zorder=5)
ax.annotate(f"< 8 °C in {t8*60:.0f} min", xy=(t8, 8), xytext=(2.1, 17), fontsize=8, color=NAVY,
            fontweight="bold", arrowprops=dict(arrowstyle="-", color=NAVY, lw=0.8))
ax.text(7.2, 9.6, "held below 8 °C for 14 h+", fontsize=8, color=TEAL, fontweight="bold", ha="center")
ax.set_xlim(0, 12); ax.set_ylim(0, 38)
ax.set_xticks([0, 2, 4, 6, 8, 10, 12]); ax.set_yticks([0, 8, 20, 35])
ax.set_xlabel("hours after sealing", fontsize=7.5, color=SLATE, labelpad=1)
ax.set_ylabel("milk °C", fontsize=7.5, color=SLATE, labelpad=1)
ax.tick_params(colors=SLATE, labelsize=7.5, length=2, pad=1.5)
for s in ("top", "right"): ax.spines[s].set_visible(False)
for s in ("left", "bottom"): ax.spines[s].set_color("#C9D6E0")
fig.savefig("ppt_slide3_chart.png")
print("t8 = %.0f min" % (t8 * 60))
