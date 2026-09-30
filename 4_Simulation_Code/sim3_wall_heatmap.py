"""
MilkShield - steady-state heat conduction through the can walls (axisymmetric FV).

Solves the temperature field in the solid parts of the can (outer PE shell,
PUF insulation, inner HDPE liner, lid, lid rim) with milk held at 4 degC inside
and 35 degC air outside. Gives:
  * a heat-map cross-section of the can
  * how much heat leaks in through side / bottom / lid
  * a geometry-based can heat leak (W/K) to cross-check the lumped model's 1.1 W/K
Geometry and conductivities are design assumptions, not a measured prototype.
"""
import sys
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

D = 1e-3                          # 1 mm cells
T_MILK, T_AMB = 4.0, 35.0
H_IN, H_OUT = 150.0, 8.0          # W/m2K milk side / still air outside
K_PE, K_PUF = 0.40, 0.025         # W/m.K

def build(puf_mm=40, lid_puf_mm=30):
    NR, NZ = 300, 600             # r 0-300 mm, z 0-600 mm
    k = np.full((NZ, NR), K_PE)
    milk = np.zeros((NZ, NR), bool)
    milk[50:560, :200] = True     # cavity r<200 mm, 50<=z<560 mm (~66 L)
    k[milk] = 0
    wall_in = 205; wall_out = wall_in + puf_mm
    shell = wall_out + 5
    k[:, shell:] = 0              # outside the can
    k[5:555, wall_in:wall_out] = K_PUF                     # side PUF
    k[5:45, :wall_out] = K_PUF                             # bottom PUF
    k[565:565 + lid_puf_mm, :wall_out] = K_PUF             # lid PUF
    k[565 + lid_puf_mm + 5:, :] = 0                        # above lid
    # rim z 555-565, r 200..shell stays solid PE -> the lid joint
    return k, milk

def solve(k, milk):
    NZ, NR = k.shape
    solid = k > 0
    idx = -np.ones(k.shape, int); idx[solid] = np.arange(solid.sum())
    rc = (np.arange(NR) + 0.5) * D
    rows, cols, vals = [], [], []
    diag = np.zeros(solid.sum()); rhs = np.zeros(solid.sum())
    zz, rr = np.nonzero(solid)
    flux_parts = {"side wall": [], "bottom": [], "lid": []}
    for (dz, dr) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        z2, r2 = zz + dz, rr + dr
        if dr:   area = (rc[rr] + dr * D / 2) * D      # radial face (per radian)
        else:    area = rc[rr] * D                     # axial face
        inside = (z2 >= 0) & (z2 < NZ) & (r2 >= 0) & (r2 < NR)
        z2c, r2c = np.clip(z2, 0, NZ - 1), np.clip(r2, 0, NR - 1)
        k1 = k[zz, rr]
        nb_solid = inside & solid[z2c, r2c]
        nb_milk = inside & milk[z2c, r2c]
        sym = (r2 < 0)                                  # axis: no flux
        nb_air = ~nb_solid & ~nb_milk & ~sym
        # solid-solid
        k2 = k[z2c, r2c]
        G = np.where(nb_solid, area / (D / (2 * k1) + D / (2 * np.where(k2 > 0, k2, 1))), 0)
        i = idx[zz, rr]; j = idx[z2c, r2c]
        m = nb_solid
        rows += list(i[m]); cols += list(j[m]); vals += list(-G[m]); np.add.at(diag, i[m], G[m])
        # boundaries
        for mask, h, Tb in ((nb_milk, H_IN, T_MILK), (nb_air, H_OUT, T_AMB)):
            Gb = area[mask] / (D / (2 * k1[mask]) + 1 / h)
            np.add.at(diag, i[mask], Gb); np.add.at(rhs, i[mask], Gb * Tb)
            if h == H_IN:
                part = np.where(dz == 1, "bottom", np.where(dz == -1, "lid", "side wall"))
                flux_parts[str(part)].append((i[mask], Gb))
    A = sp.csr_matrix((vals + list(diag), (rows + list(range(len(diag))), cols + list(range(len(diag))))))
    T = spla.spsolve(A, rhs)
    Q = {p: sum(2 * np.pi * np.sum(Gb * (T[ii] - T_MILK)) for ii, Gb in lst) for p, lst in flux_parts.items()}
    Tf = np.full(k.shape, np.nan); Tf[solid] = T; Tf[milk] = T_MILK
    return Tf, Q

def ua_of(puf_mm):
    k, milk = build(puf_mm)
    _, Q = solve(k, milk)
    return sum(Q.values()) / (T_AMB - T_MILK), Q

if __name__ == "__main__":
    k, milk = build(40)
    T, Q = solve(k, milk)
    tot = sum(Q.values()); ua = tot / (T_AMB - T_MILK)
    print(f"Heat leak into milk at 35 C outside / 4 C milk (40 mm PUF): {tot:.1f} W  -> UA = {ua:.2f} W/K")
    for p, q in Q.items(): print(f"   {p:10s} {q:5.1f} W  ({q/tot*100:4.1f} %)")
    print(f"   12 h leak = {tot*12*3600/1e6:.2f} MJ  (deck estimate 1.4 MJ)")
    for mm in (20, 60):
        u, _ = ua_of(mm); print(f"   side-wall PUF {mm} mm (bottom 40, lid 30 fixed) -> UA = {u:.2f} W/K")

    k2, m2 = build(40); k2[555:565, 205:245] = K_PUF
    q2 = sum(solve(k2, m2)[1].values())
    print(f"   if the lid joint were insulated too: {q2:.1f} W -> solid-plastic rim costs {tot-q2:.1f} W ({(tot-q2)/tot*100:.0f}%)")

    cmap = LinearSegmentedColormap.from_list("coldhot", ["#1c5cab", "#8fb8e8", "#f2f1ec", "#f0a57d", "#c2410c"])
    full = np.hstack([T[:, 249::-1], T[:, :250]])   # mirror to show the whole section
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 7), dpi=150, gridspec_kw={"width_ratios": [1.25, 1]})
    im = a1.imshow(full, origin="lower", cmap=cmap, vmin=4, vmax=35, extent=[-250, 250, 0, 600])
    a1.text(0, 300, "MILK\n(held at 4 °C)", ha="center", va="center", fontsize=12, color="#0b0b0b")
    a1.text(-245, 612, "outside air 35 °C", fontsize=10, color="#52514e")
    a1.annotate("lid joint\n(warm spot)", xy=(222, 560), xytext=(120, 470), fontsize=10,
                arrowprops=dict(arrowstyle="->", color="#0b0b0b"))
    a1.annotate("40 mm PUF", xy=(-225, 250), xytext=(-195, 150), fontsize=10,
                arrowprops=dict(arrowstyle="->", color="#0b0b0b"))
    a1.set_xlabel("mm"); a1.set_ylabel("mm"); a1.set_xlim(-260, 260); a1.set_ylim(-5, 630)
    a1.set_title("Can cross-section: temperature in the walls", loc="left", fontsize=12)
    # zoom on lid joint with heat-flow arrows
    z0, z1, r0, r1 = 520, 600, 180, 250
    sub = T[z0:z1, r0:r1]
    a2.imshow(sub, origin="lower", cmap=cmap, vmin=4, vmax=35, extent=[r0, r1, z0, z1])
    gz, gr = np.gradient(np.nan_to_num(sub, nan=T_MILK))
    kk = k[z0:z1, r0:r1]
    qz, qr = -kk * gz, -kk * gr
    s = 4
    R, Z = np.meshgrid(np.arange(r0, r1) + 0.5, np.arange(z0, z1) + 0.5)
    msk = (kk > 0)[::s, ::s]
    a2.quiver(R[::s, ::s][msk], Z[::s, ::s][msk], qr[::s, ::s][msk], qz[::s, ::s][msk],
              color="#0b0b0b", scale=None, width=0.004)
    a2.text(185, 530, "milk", fontsize=11); a2.text(205, 590, "lid", fontsize=11)
    a2.set_title("Zoom: lid joint - arrows = heat flow", loc="left", fontsize=12)
    a2.set_xlabel("radius (mm)"); a2.set_ylabel("height (mm)")
    cb = fig.colorbar(im, ax=[a1, a2], shrink=0.8, pad=0.02); cb.set_label("Temperature (°C)")
    brk = ", ".join(f"{p} {q/tot*100:.0f}%" for p, q in Q.items())
    fig.text(0.01, 0.015, f"Steady state, axisymmetric, 1 mm grid. Heat leak {tot:.1f} W = {ua:.2f} W/K ({brk}). "
             "Assumed k: PUF 0.025, PE 0.40 W/m·K; air h 8, milk h 150 W/m²K. Design estimate.", fontsize=8, color="#52514e")
    fig.savefig("sim3_wall_heatmap.png", bbox_inches="tight")
    print("saved sim3_wall_heatmap.png")
