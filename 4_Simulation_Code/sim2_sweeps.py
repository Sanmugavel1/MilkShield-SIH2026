"""
MilkShield - parameter sweeps on the lumped model (milkshield_sim.py).
  A. cartridge count  -> hours the milk stays <= 8 degC
  B. ambient 25/35/45 degC
  C. insulation: bare aluminium can vs 20/40/60 mm PUF
All inputs are assumptions (see milkshield_sim.py); this is a design estimate.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from milkshield_sim import simulate, ICE_KG

INK, INK2, GRID = "#0b0b0b", "#52514e", "#e6e5e0"
C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
H24 = 24.0
A_CAN = 0.94          # m2 outer area, ~0.40 m dia x 0.55 m can
BRIDGE = 0.5          # W/K lid, gasket, handles (assumed; makes 40 mm = deck's 1.1 W/K)

def ua_puf(mm):  return A_CAN * 0.025 / (mm / 1000) + BRIDGE
UA_BARE_AL = 7.5      # W/K, bare Al can, still air h ~ 8 W/m2K (assumed)

def hold_hours(t, T):
    """Hours the milk spends at or below 8 degC (counting from sealing)."""
    return float(np.sum(T <= 8.0) * (t[1] - t[0]))

def style(ax, title, xlabel, ylabel):
    ax.set_title(title, loc="left", fontsize=12, color=INK)
    ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)
    ax.grid(axis="y", color=GRID, lw=0.8); ax.set_axisbelow(True)
    for s in ("top", "right"): ax.spines[s].set_visible(False)

def end_labels(ax, items, x):
    for (lab, y, c) in items:
        ax.plot([x + 0.2, x + 0.8], [y, y], color=c, lw=3, clip_on=False)
        ax.text(x + 1.0, y, lab, va="center", fontsize=9, color=INK)

def foot(fig, txt):
    fig.text(0.01, 0.01, txt, fontsize=8, color=INK2)

# ---------- A. cartridge count ----------
fig, ax = plt.subplots(figsize=(11, 6.2), dpi=150)
ns = np.arange(0, 13)
cases = [("Fresh 40 L (35 °C)", 40, 35.0), ("Fresh 30 L (35 °C)", 30, 35.0), ("Pre-chilled 40 L (6 °C)", 40, 6.0)]
print("A. hours <= 8 degC over a 24 h trip, 35 degC ambient")
print("   n  " + "  ".join(f"{c[0]:>24s}" for c in cases))
table = []
for (lab, L, T0), c in zip(cases, C):
    hrs = [hold_hours(*simulate(L, n, T0, hours=H24)[:2]) for n in ns]
    table.append(hrs)
    ax.plot(ns, hrs, color=c, lw=2, marker="o", ms=6)
for n in ns:
    print(f"  {n:2d}  " + "  ".join(f"{table[i][n]:24.1f}" for i in range(3)))
ax.axhline(12, color=INK2, lw=1, ls="--"); ax.text(0.1, 12.4, "12 h target", fontsize=9, color=INK2)
ax.axhline(6, color=INK2, lw=1, ls=":");   ax.text(0.1, 6.4, "6 h target", fontsize=9, color=INK2)
ax.set_xticks(ns, [f"{n}\n{n*ICE_KG:.0f} kg" for n in ns])
ax.set_xlim(-0.3, 12.3); ax.set_ylim(0, 25)
end_labels(ax, [(cases[i][0], table[i][-1] + d, C[i]) for i, d in zip(range(3), (-1.6, 0, 1.6))], 12.3)
style(ax, "How many cartridges? Hours milk stays at or below 8 °C (24 h trip, 35 °C ambient)",
      "Cartridges loaded (and ice weight carried)", "Hours at or below 8 °C")
foot(fig, "Lumped model, assumed inputs (h_milk 150 W/m²K, can heat leak 1.1 W/K, 2 kg ice per cartridge from -10 °C). Design estimate, not test data.")
fig.subplots_adjust(right=0.8, bottom=0.16)
fig.savefig("sim2a_cartridge_count.png"); plt.close(fig)

# ---------- B. ambient temperature ----------
fig, ax = plt.subplots(figsize=(11, 6.2), dpi=150)
ax.axhspan(4, 8, color="#1baf7a", alpha=0.10, lw=0)
print("\nB. fresh 40 L, 8 cartridges, ambient sweep")
items = []
for amb, c in zip((25, 35, 45), (C[0], C[3], C[1])):
    t, T, mf = simulate(40, 8, 35.0, hours=H24, t_amb=float(amb))
    ax.plot(t, T, color=c, lw=2)
    items.append((f"{amb} °C ambient", T[-1], c))
    print(f"   {amb} C: hours<=8C {hold_hours(t,T):5.1f}  milk @24h {T[-1]:5.1f} C  ice melted {mf[-1]*100:4.0f}%")
items.sort(key=lambda x: x[1]); ys = [items[0][1]]
for it in items[1:]: ys.append(max(it[1], ys[-1] + 2.2))
end_labels(ax, [(l, y, c) for (l, _, c), y in zip(items, ys)], 24)
ax.set_xlim(0, 24); ax.set_ylim(0, 37); ax.set_xticks(range(0, 25, 4))
style(ax, "Hot days: fresh 40 L with 8 cartridges at different ambient temperatures (milk starts at 35 °C)",
      "Hours after sealing", "Milk temperature (°C)")
foot(fig, "Green band = 4-8 °C target. Lumped model, assumed inputs. Design estimate, not test data.")
fig.subplots_adjust(right=0.74, bottom=0.12)
fig.savefig("sim2b_ambient.png"); plt.close(fig)

# ---------- C. insulation ----------
fig, ax = plt.subplots(figsize=(11, 6.2), dpi=150)
ax.axhspan(4, 8, color="#1baf7a", alpha=0.10, lw=0)
print("\nC. fresh 40 L, 8 cartridges, 35 C, insulation sweep")
opts = [("Bare aluminium can + ice", UA_BARE_AL, C[1]), ("20 mm PUF", ua_puf(20), C[3]),
        ("40 mm PUF (design)", ua_puf(40), C[0]), ("60 mm PUF", ua_puf(60), C[2])]
items = []
for lab, ua, c in opts:
    t, T, mf = simulate(40, 8, hours=H24, ua_wall=ua)
    ax.plot(t, T, color=c, lw=2)
    items.append((f"{lab}  ({ua:.1f} W/K)", T[-1], c))
    print(f"   {lab:32s} UA {ua:4.2f} W/K  hours<=8C {hold_hours(t,T):5.1f}  milk @24h {T[-1]:5.1f} C")
items.sort(key=lambda x: x[1]); ys = [items[0][1]]
for it in items[1:]: ys.append(max(it[1], ys[-1] + 2.2))
end_labels(ax, [(l, y, c) for (l, _, c), y in zip(items, ys)], 24)
ax.set_xlim(0, 24); ax.set_ylim(0, 37); ax.set_xticks(range(0, 25, 4))
style(ax, "Why insulation matters: same 8 cartridges, different can walls (35 °C ambient)",
      "Hours after sealing", "Milk temperature (°C)")
foot(fig, "Can heat leak = area x k / thickness + 0.5 W/K for lid/handles (assumed). Bare Al can: still-air h ≈ 8 W/m²K, no sun. Design estimate, not test data.")
fig.subplots_adjust(right=0.74, bottom=0.12)
fig.savefig("sim2c_insulation.png"); plt.close(fig)
print("\nsaved sim2a/b/c PNGs")
