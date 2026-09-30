"""
MilkShield - lumped-parameter thermal simulation (SIH 2026, PS 26110).

Two thermal masses:
  * milk (well-mixed, one temperature)
  * N ice cartridges (tracked by enthalpy so melting at 0 degC is handled)
Heat flows:  ambient --(UA_wall)--> milk --(N * UA_cart)--> cartridges

This is a DESIGN ESTIMATE, not validation. Every parameter below is an
assumption; the shaded band shows how much the answer moves when the two
most uncertain ones (h_milk, UA_wall) change. Replace them with measured
values after the water-proxy test.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------------- assumptions (edit these) ----------------
T_AMB      = 35.0      # degC ambient (deck basis)
RHO_MILK   = 1.032     # kg/L          [8]
CP_MILK    = 3930.0    # J/kg.K        [8]
ICE_KG     = 2.0       # kg water per 2 L cartridge
T_ICE0     = -10.0     # degC cartridge temp when loaded (freezer -18, warms in handling)
CP_ICE, CP_WATER, L_FUS = 2050.0, 4186.0, 334e3
A_CART     = 0.11      # m2 wetted area of one 2 L cylinder (~80 mm dia x 400 mm)
WALL_T, WALL_K = 0.002, 0.45   # HDPE cartridge wall, m and W/m.K
H_MILK     = 150.0     # W/m2K natural convection milk side (uncertain: 75-300)
H_INSIDE   = 200.0     # W/m2K ice/meltwater side
UA_WALL    = 1.1       # W/K can heat leak, 40 mm PUF incl. lid (deck: 1.4 MJ / 12 h)
HOURS, DT  = 12.0, 10.0

def ua_cart(h_milk):
    return A_CART / (1/h_milk + WALL_T/WALL_K + 1/H_INSIDE)

def ice_temp(H, m):
    """Cartridge temperature from enthalpy H (J, 0 = solid ice at 0 degC)."""
    if H < 0:              return H / (m * CP_ICE)
    if H < m * L_FUS:      return 0.0
    return (H - m * L_FUS) / (m * CP_WATER)

def simulate(litres, n_cart, t_milk0=35.0, h_milk=H_MILK, ua_wall=UA_WALL, hours=HOURS, t_amb=T_AMB):
    m_milk = litres * RHO_MILK
    C_milk = m_milk * CP_MILK
    m_ice  = n_cart * ICE_KG
    H      = m_ice * CP_ICE * T_ICE0 if n_cart else 0.0
    UAc    = n_cart * ua_cart(h_milk)
    Tm     = t_milk0
    steps  = int(hours * 3600 / DT)
    t, Tmilk, melted = np.zeros(steps+1), np.zeros(steps+1), np.zeros(steps+1)
    Tmilk[0] = Tm
    for k in range(steps):
        Tc   = ice_temp(H, m_ice) if n_cart else Tm
        q_in = ua_wall * (t_amb - Tm)          # leak into milk
        q_c  = UAc * (Tm - Tc)                 # milk -> cartridges
        Tm  += (q_in - q_c) * DT / C_milk
        H   += q_c * DT
        t[k+1], Tmilk[k+1] = (k+1)*DT/3600, Tm
        melted[k+1] = np.clip(H / (m_ice*L_FUS), 0, 1) if n_cart else 0
    return t, Tmilk, melted

def summary(t, T):
    below = T <= 8.0
    t8 = t[np.argmax(below)] if below.any() else None
    back = t8 is not None and (T[t >= t8] > 8.0).any()
    return t8, back, T.min(), T[-1]

SCENARIOS = [  # label, litres, cartridges, start temp
    ("Fresh 40 L, 11 cartridges", 40, 11, 35.0),
    ("Fresh 30 L, 8 cartridges",  30,  8, 35.0),
    ("Pre-chilled 40 L, 3 cartridges", 40, 3, 6.0),
    ("Fresh 40 L, no cartridges (insulated only)", 40, 0, 35.0),
]
COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#52514e"]

if __name__ == "__main__":
    fig, ax = plt.subplots(figsize=(11, 6.2), dpi=150)
    ax.axhspan(4, 8, color="#1baf7a", alpha=0.10, lw=0)
    ax.text(11.9, 8.6, "4-8 °C target band", ha="right", va="center", fontsize=10, color="#52514e")

    # uncertainty band for the headline case
    runs = [simulate(40, 11, h_milk=h, ua_wall=u)[1]
            for h in (75, 150, 300) for u in (0.8, 1.1, 1.6)]
    t = simulate(40, 11)[0]
    ax.fill_between(t, np.min(runs, 0), np.max(runs, 0), color=COLORS[0], alpha=0.15, lw=0)

    print(f"{'scenario':46s} {'<=8C at':>8s} {'rises >8C again':>16s} {'min':>6s} {'@12h':>6s} {'ice melted':>10s}")
    label_y = [0.2, 3.2, 6.2, 35.0]   # hand-staggered so end labels don't collide
    for (label, L, n, T0), c, ly in zip(SCENARIOS, COLORS, label_y):
        t, T, mf = simulate(L, n, T0)
        ax.plot(t, T, color=c, lw=2)
        ax.plot([12.1, 12.4], [ly, ly], color=c, lw=3, clip_on=False)
        ax.text(12.5, ly, label, color="#0b0b0b", fontsize=9, va="center")
        t8, back, tmin, tend = summary(t, T)
        print(f"{label:46s} {('%.2f h' % t8) if t8 is not None else 'never':>8s} "
              f"{'yes' if back else 'no':>16s} {tmin:6.1f} {tend:6.1f} {mf[-1]*100:9.0f}%")

    ax.set_xlim(0, 12); ax.set_ylim(0, 37)
    ax.set_xlabel("Hours after sealing"); ax.set_ylabel("Milk temperature (°C)")
    ax.set_title("MilkShield - simulated milk temperature, 35 °C ambient (design estimate, not test data)",
                 loc="left", fontsize=12)
    ax.grid(axis="y", color="#e6e5e0", lw=0.8); ax.set_axisbelow(True)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    fig.text(0.01, 0.01, "Shaded blue band: fresh 40 L case with h_milk 75-300 W/m²K and can heat leak 0.8-1.6 W/K. "
             "Lumped model, well-mixed milk; all inputs assumed.", fontsize=8, color="#52514e")
    fig.subplots_adjust(right=0.72, bottom=0.13)
    fig.savefig("milkshield_sim.png")
    print("saved milkshield_sim.png")

    # minimum cartridges: milk reaches <=8 degC within 2 h and stays there to the hold time
    print("\nMinimum cartridges (<=8 degC within 2 h, held to end):")
    for label, L, T0, hrs in [("Fresh 40 L, 12 h", 40, 35, 12), ("Fresh 30 L, 6 h", 30, 35, 6),
                              ("Pre-chilled 40 L, 12 h", 40, 6, 12)]:
        for n in range(0, 20):
            t, T, _ = simulate(L, n, T0)
            m = t <= hrs
            if (T[(t >= 2) & m] <= 8).all():
                print(f"  {label:24s} {n:2d} cartridges  (min {T[m].min():.1f} degC)"); break
